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


The basic building block of the AXI4 protocol is a single-cycle transfer of data on a single channel between a sender and a receiver. It uses a valid/ready protocol with the sender driving the valid signal and the receiver driving the ready signal. A data transfer occurs on every cycle where ready and valid are both high. There are several constraints on valid and ready:


valid:
 - Must be low in reset.
 - Once asserted, valid must remain high until the transfer happens.
 - Must not depend on ready.

ready:
 - Not required to be independent of valid but recommended to be so that transfers happen in a single cycle.

The dependency constraints on valid and ready mean that combinational paths from ready to valid are not allowed which prevents combinational loops (valid to ready paths are allowed). Further, the sender cannot wait for the receiver's ready to go high and then assert valid in the next cycle. This is to prevent deadlocks where both sides are waiting for the other to set their ready/valid. Ready is allowed to wait for valid.



Example 32-bit 2-element FIFO showing both sender and receiver-side code:


```systemverilog
module fifo2(input aclk, input aresetn,
             input logic[31:0] wdata, input wvalid, output wready,
             output logic[31:0] rdata, output rvalid, input rready);


logic [31:0] d0, d1;
logic rptr, wptr;
logic [1:0] level;


assign wready = level != 2;
assign rvalid = level != 0;
assign rdata = rptr == 0 ? d0 : d1;


wire do_read = rvalid && rready;
wire do_write = wvalid && wready;


always_ff @(posedge aclk or negedge aresetn) begin
  if (aresetn == 0) begin
    d0 <= 32’b0;
    d1 <= 32’b1;
    rptr <= 1’b0;
    wptr <= 1’b0;
    level <= 2’b0;
  end else begin
    rptr <= rptr + do_read;
    wptr <= wptr + do_write;
    level <= level + do_write - do_read;
    if (do_write && wptr == 0)
      d0 <= wdata;
    if (do_write && wptr == 1)
      d1 <= wdata;
  end
end
endmodule
```


## Transaction


A transaction is initiated by the manager (deprecated term: master, alternate term: requester) to read data from or write data to the subordinate (old term: slave, alternate term: completer.


 - Read: Manager makes 1 transfer on the AR channel for address, burst length (N), etc. Subordinate makes N transfers on the R channel for data.
 - Write: Manager makes 1 transfer on the AW channel for address, burst length (N), etc. and N transfers on the W channel for data. Subordinate makes 1 transfer on the B channel for response.

See the wiki page for a list of signals on these 5 channels (AR, R, AW, W, B).

The N transfers/beats are together called a burst. The (1 + N) transfers for read constitute a complete read transaction and the (1 + N + 1) transfers for write constitute a complete write transaction.


### Burst type

Each transaction has a burst type: FIXED, INCR, WRAP sent on the AxBURST signal. The burst type determines some aspects of how data and addresses are used as described later.


### Data width


Read and write data buses are 1 - 128 bytes wide (in powers of 2). A manager can initiate transactions that are do not use the full data bus. The is done using the AxSIZE signal but it is limited to the same set of widths (1 to 128 bytes in powers of 2).


### Addresses


The transaction address AxADDR is a byte-address. For FIXED and INCR, the address can be a multiple of 1. For WRAP, the address has to be a multiple of (1 << AxSIZE). 

Using AxADDR, the implicit address of each beat can be calculated as shown in the table below. ("Implicit address" is not a standard term. I made it up for my understanding.)


Consider a transaction with the following characteristics:


Size of each beat: S = (1 << AxSIZE) bytes
Address: AxADDR   (must be a multiple of S for WRAP, unconstrained for others)
Burst length: AxLEN + 1 (must be 2, 4, 8, 16 for WRAP, unconstrained for others)
Total transaction size = TS = S * (AxLEN + 1)


| Burst mode | Beat index | Implicit address of a beat |
| ---------- | ---------- | -------------------------- |
| FIXED  | i = 0 to AxLEN | AxADDR |
| INCR   | 0              | AxADDR |
| INCR   | i = 1 to AxLEN | AxADDR - (AxADDR % S) + i * S |
| WRAP   | i = 0 to AxLEN | AxADDR - (AxADDR % TS) + (AxADDR + i * S) % TS |


The implicit addresses in a burst cannot cross a 4kB boundary. The manager must ensure this by limiting AxLEN as needed.


### Data alignment

The data transferred on the bus is always aligned to the bus width (and not the beat size S = 1 << AxSIZE). That is, if the data bus is DS bytes wide, the bytes on the data bus always have the following addresses:


| Bit range | Address |
| --------- | ------- |
| [7:0]     | n * DS  |
| [15:8]    | n * DS + 1 |
| [8k+7 : 8k] | n * DS + k |
| [8DS-1 : 8DS - 8] | n * DS + DS - 1 |

(n is any integer)


The alignment is maintained by adjusting the starting bit index and number of bytes transferred in a beat based on the implicit address of the beat. This is shown in the equations below:


Implicit beat address = addr
Starting bit index = 8 * (addr - addr % DS)
Number of bytes transferred = S - (addr % S)


Note that DS  >= S and DS is also a power of 2. Thus, DS is a multiple of S.


In particular, for the INCR burst, the first beat may transfer less than S bytes if AxADDR is not aligned to S. The remaining beats will always transfer S bytes. For FIXED, all beats may transfer less than S bytes if AxADDR is not aligned to S. For WRAP, AxADDR is required to be aligned to S.


The function for calculating the implicit beat address based on the starting address, burst type, beat size:


```systemverilog
function logic [AddrBits-1:0] beat_addr(
  input logic [AddrBits-1:0] axaddr,
  input axi_pkg::burst_t axburst,
  input logic [2:0] axsize,
  input logic [7:0] axlen,
  input logic [7:0] beat_index
);
logic [AddrBits-1:0] out, mask;


if (axburst == kFixed) beat_index = 0;
out = axaddr + (beat_index << axsize);


if (axburst == kIncr && beat_index > 0) begin
  // Align to beat size by keeping MSBs only.
  mask = (1 << axsize) - 1;
  out = out & ~mask;
end else if (axburst == kWrap) begin
  // Keep LSBs from address and get MSBs from wrap boundary.
  // axaddr is required to be aligned to axsize in wrap mode.
  // mask + 1 is a power of 2 as axlen + 1 is 2,4,8,16 in wrap mode.
  mask = ((axlen + 1) << axsize) - 1;
  out = (out & mask) | (axaddr & ~mask);
end


return out;
endfunction
```
