# Basics of AXI4


This doc is based on the following sources -

 - [AMBA AXI and ACE Protocol Specification](https://developer.arm.com/documentation/ihi0022/latest/) ("spec")
 - [Advanced eXtensible Interface - Wikipedia](https://en.wikipedia.org/wiki/Advanced_eXtensible_Interface) ("wiki page")

The wiki page is a nice and gentle introduction to AXI4. The spec is readable too (although a little verbose). This doc is an attempt to summarize and simplify some of the details and provides code examples as a supplement to the text and figure-based explanations of the spec and wiki page.


## Clock and reset


Should be used as follows:


```systemverilog
always_ff @(posedge ACLK or negedge ARESETn) begin
  if (ARESETn == 0)
    dff <= reset_val;
  else
    dff <= next_val;
end
```


Thus, the AXI4 node goes into reset on the negative edge of ARESETn and exits reset on the positive edge of ACLK in which ARESETn is high.


## Transfer / Beat


The basic building block of the AXI4 protocol is a single-cycle transfer of data on a single channel between a sender and a receiver. It uses a valid/ready protocol with the sender driving the valid signal and the receiver driving the ready signal. A data transfer occurs on every cycle where ready and valid are both high. There are several constraints on the valid signal:

 - Valid must be low in reset.
 - Once asserted, valid must remain high until the transfer happens. The data being transferred must also remain unchanged during this time.
 - Valid must not depend on ready. This means no combinational paths from ready to valid. Further, the sender must not wait for the receiver's ready to go high before asserting valid in a future cycle. 

The ready signal does not these constraints - valid to ready paths are allowed and the receiver can wait for the sender's valid to go high before asserting ready in the same or a future cycle. When ready is asserted, it can be deasserted at any time.

The dependency constraints on valid help to avoid combinational loops and prevent deadlocks where both sides are waiting for the other to set their ready/valid.

Example 32-bit 2-element FIFO showing both sender and receiver-side code:


```systemverilog
module fifo2(input aclk, input aresetn,
             input logic[31:0] wdata, input wvalid, output wready,
             output logic[31:0] rdata, output rvalid, input rready);

logic [31:0] mem[0:3];
logic [1:0] rptr, wptr;
logic [2:0] level;

assign wready = level != 4;
assign rvalid = level != 0;
assign rdata = mem[rptr];

wire do_read = rvalid && rready;
wire do_write = wvalid && wready;

always_ff @(posedge aclk or negedge aresetn) begin
  if (aresetn == 0) begin
    rptr <= 1’b0;
    wptr <= 1’b0;
    level <= 2’b0;
  end else begin
    if (do_write) mem[wptr] <= wdata;
    rptr <= rptr + do_read;
    wptr <= wptr + do_write;
    level <= level + do_write - do_read;
  end
end
endmodule
```

## Transaction

AXI4 uses point-to-point connections - there is no physical "bus" on which multiple nodes sit. Each connection has a manager node (deprecated term: master, alternate term: requester) and a subordinate node (deprecated term: slave, alternate term: completer). There are 3 channels going from the manager to the subordinate (AR, AW, W) and 2 channels the other way (R, B). The [wiki page](https://en.wikipedia.org/wiki/Advanced_eXtensible_Interface#Signals) has a list of signals on these 5 channels.

The manager initiates read and write transactions as follows:

 - Read: Manager makes 1 transfer on the AR channel with address, burst length (N), etc. Subordinate makes N transfers on the R channel for data.
 - Write: Manager makes 1 transfer on the AW channel with address, burst length (N), etc. and N transfers on the W channel for data. Subordinate makes 1 transfer on the B channel for response.

In the context of the N transfers for data on R and W channels, each transfer is also called a beat.

Transactions have four key parameters transmitted on AR and AW channels: AxBURST, AxADDR, AxLEN and AxSIZE (x = R or W).

 - AxBURST : Burst type. One of FIXED, INCR, [WRAP](#wrap-bursts). Determines the [address increment logic](#address-increment-logic) for N > 1 bursts.
 - AxADDR : Starting byte-address. Can be a multiple of 1 for FIXED and INCR, and multiple of (1 << AxSIZE) for WRAP.
 - AxLEN : 8-bit value for (burst length - 1). For FIXED, 1 to 16 beats are allowed. For INCR, 1 to 256 beats are allowed. For WRAP, only 2, 4, 8 or 16 beats are allowed.
 - AxSIZE : 3-bit value for log2(beat size in bytes). Beat size can be one of 1, 2, 4, 8, ... byte-width of the data bus (i.e. byte-width of RDATA and WDATA signals). Byte-width of the data bus is at most 128 and is also limited to powers of 2. The actual number of bytes transferred in a beat can be less than (1 << AxSIZE) due to [data alignment requirement](#data-alignment-requirements) and write data strobes.

These parameters are also constrained such that the burst does not cross a 4kB address boundary.

### Address increment logic

Given AxBURST, AxADDR, AxLEN and AxSIZE, the starting address of each beat and the number of bytes transferred in each beat can be calculated as follows.

```
Beat size: S = (1 << AxSIZE) bytes
Transaction size = TS = S * (AxLEN + 1) bytes
```

| AxBURST | Beat index | Starting address of beat | Num. bytes transferred in beat |
| ---------- | ---------- | ----------------------- | ---------------------- |
| FIXED  | i = 0 to AxLEN | `AxADDR` | `S - (AxADDR % S)` |
| INCR   | 0              | `AxADDR` | `S - (AxADDR % S)` |
| INCR   | i = 1 to AxLEN | `AxADDR - (AxADDR % S) + i * S` | `S` | 
| WRAP   | i = 0 to AxLEN | `AxADDR - (AxADDR % TS) + (AxADDR + i * S) % TS` | `S` |

Or, in code

```systemverilog
typedef enum {FIXED, INCR, WRAP} BurstType;

function logic [AddrBits-1:0] beat_start_address(
  input logic [AddrBits-1:0] axaddr,
  input BurstType axburst,
  input logic [2:0] axsize,
  input logic [7:0] axlen,
  input logic [7:0] beat_index
);
  logic [AddrBits-1:0] out, mask;

  if (axburst == FIXED) beat_index = 0;
  out = axaddr + (beat_index << axsize);

  if (axburst == INCR && beat_index > 0) begin
    mask = (1 << axsize) - 1;
    out = out & ~mask;  // truncate axsize LSBs to 0.
  end else if (axburst == WRAP) begin
    // Keep LSBs from address and get MSBs from wrap boundary.
    // mask + 1 is a power of 2 as axlen + 1 is 2,4,8,16 in wrap mode.
    mask = ((1 + axlen) << axsize) - 1;
    out = (out & mask) | (axaddr & ~mask);
  end

  return out;
endfunction
```

Note that the number of bytes transferred in a beat can be calculated in general as `S - (starting address of beat % S)`.

### Data alignment requirements

Data on the bus is always aligned to the bus width and not the beat size S = 1 << AxSIZE. That is, if the data bus is DS bytes wide, the bytes on the data bus always have the following addresses:


| Bit range | Address |
| --------- | ------- |
| [7:0]     | n * DS  |
| [15:8]    | n * DS + 1 |
| [8k+7 : 8k] | n * DS + k |
| [8DS-1 : 8DS - 8] | n * DS + DS - 1 |

(n is any integer)

For example, if a request is sent on a 16-byte data bus with the following parameters:

```
AxBURST = INCR
AxADDR = 7
AxSIZE = 2 (4 bytes per beat)
AxLEN = 4 (5 beats)
```

the data transferred on the bus will have the following addresses on the 5 beats:

| Bit range | Beat 0 | Beat 1 | Beat 2 | Beat 3 | Beat 4 |
| --------- | ---- | ---- | ---- | ---- | ---- |
| [7:0]     |      |      |      |   16 |      |
| [15:8]    |      |      |      |   17 |      |
| [23:16]   |      |      |      |   18 |      |
| [31:24]   |      |      |      |   19 |      |
| [39:32]   |      |      |      |      |   20 |
| [47:40]   |      |      |      |      |   21 |
| [55:48]   |      |      |      |      |   22 |
| [63:56]   |    7 |      |      |      |   23 |
| [71:64]   |      |    8 |      |      |      |
| [79:72]   |      |    9 |      |      |      |
| [87:80]   |      |   10 |      |      |      |
| [95:88]   |      |   11 |      |      |      |
| [103:96]  |      |      |   12 |      |      |
| [111:104] |      |      |   13 |      |      |
| [119:112] |      |      |   14 |      |      |
| [127:120] |      |      |   15 |      |      |


### WRAP bursts

The address increment logic for WRAP bursts can be explained as follows. For a transaction size of `TS = (AxLEN + 1) << AxSIZE`, split the address space into TS-byte chunks aligned to TS i.e. 0 to TS-1, TS to 2TS-1, 2TS to 3TS-1, .... Find the chunk that contains AxADDR and start reading from/writing to AxADDR and incrementing by `1 << AxSIZE` every beat. If you reach the end of the chunk before you reach the end of the burst, wrap around to the start of the chunk and read until AxADDR - 1.

The starting address of the chunk is `AxADDR - (AxADDR % TS)` and the offset within the chunk for the i'th beat is `(AxADDR + (i << AxSIZE)) % TS` giving the beat address as:

```
i'th beat address = AxADDR - (AxADDR % TS) + (AxADDR + (i << AxSIZE)) % TS
```
