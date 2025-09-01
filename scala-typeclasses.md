# How to use the Scala typeclass pattern in Chisel

As a motivating example, let us design a priority arbiter for DecoupledIO.
But it should also extensible to user-defined interfaces like request-grant.

## A generic priority-arbiter

In Arbiter.scala:

```scala
import chisel3._
import chisel3.util.{DecoupledIO, PriorityEncoderOH}

// Given a client of type `A`, this trait defines the abstract interface for
// how to get a request from the client and send a grant back.
trait Arbitrable[A] {
  def request(a: A): Bool
  def grant(a: A, value: Bool): Unit
}

object Arbitrable {
  // Define an instance of Arbitrable for DecoupledIO
  implicit def arbitrableDecoupledIO[T <: Data]: Arbitrable[DecoupledIO[T]] =
    new Arbitrable[DecoupledIO[T]] {
      def request(a: DecoupledIO[T]): Bool = a.valid
      def grant(a: DecoupledIO[T], value: Bool): Bool = a.ready :#= value
    }
}

// An arbiter that works with any client bundle `A` that has an instance of `Arbitrable[A]`
class PriorityArbiter[A <: Data : Arbitrable](numClients: Int, clientType: A) extends Module {
  val io = IO(Flipped(Vec(numClients, clientType)))

  // `implicitly` is a Scala function that magically finds an instance of `Arbitrable[A]`.
  // Will throw a compile-time error if it cannot find any such instance.
  val arbitrable = implicitly[Arbitrable[A]]

  // Use `arbitrable` to get requests and send grants.
  val requests = io.map(arbitrable.request(_))
  val grants = PriorityEncoderOH(requests)

  for ((client, grant) <- io.zip(grants)) {
    arbitrable.grant(client, grant)
  }
}
```

Let us now define a custom `ReqGrantClient` interface that also works with our arbiter.
In ReqGrantClient.scala:

```scala
class ReqGrantClient extends Bundle {
  val request = Bool()
  val grant = Flipped(Bool())
}

object ReqGrantClient {
  implicit val arbitrable: Arbitrable[ReqGrantClient] =
    new Arbitrable[ReqGrantClient] {
      def request(a: ReqGrantClient): Bool = a.request
      def grant(a: ReqGrantClient, value: Bool) = a.grant :#= value
    }
}
```

To use our arbiter in RTL code:

```scala
val reqGrantClients = Vec(4, new ReqGrantClient)
val reqGrantArbiter = Module(new PriorityArbiter(4, new ReqGrantClient))
reqGrantClients.io :<>= reqGrantClients

val decoupledClients = Vec(4, new DecoupledIO(UInt(8.W)))
val decoupledArbiter = Module(new PriorityArbiter(4, new DecoupledIO(8.W)))
decoupledArbiter.io :<>= decoupledClients
```

## How it works

All the magic happens in the `implicitly` function. It is pre-defined in Scala as:

```scala
def implicitly[T](implicit e: T): T = e
```

In the arbiter module, when the compiler encounters `val arbitrable = implicitly[Arbitrable[A]]`,
it will look for a value of type `Arbitrable[A]`. In particular, it will look for that value
in the companion object of `Arbitrable` and of `A`. For `ReqGrantClient`, which we defined,
we put the value in its companion object. But since `DecoupledIO` is defined in Chisel, we put
its instance in the companion object of `Arbitrable`. 

Note also, that the instance of `Arbitrable[DecoupledIO[T]]` is defined as a `def` since we
need a different instance for each `T` (even though we do not use `T` anywhere). For
`Arbitrable[ReqGrantClient]`, we only need a single instance which can be a `val`.

## When to use typeclasses

We can think of typeclasses as a more extensible class-inheritance system. In the above example,
we could have defined `Arbitrable` as a trait that all clients bundles have to extend -

```scala
trait Arbitrable {
  def request: Bool
  def grant: Bool  // flipped
}
```

But that would not work for types like `DecoupledIO` that we did not define. With typeclasses,
we define an abstract interface that any client type can implement to make it compatible with 
`PriorityArbiter`.

## Resources

This note is essentially a concise version of an as-yet unposted blog on the Chisel website -
https://github.com/chipsalliance/chisel/pull/4913/files. Some resources mentioned there -

 - [Scala book](https://docs.scala-lang.org/scala3/book/ca-type-classes.html)
 - Chisel's `dataview` feature uses typeclasses as explained
   [here](https://www.chisel-lang.org/docs/explanations/dataview#type-classes)
