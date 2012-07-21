
## GLBackend design

/Creational pattern instead of inheritance based pattern/

Creational patterns become important as systems evolve to depend moreon object
composition than class inheritance. As that happens,emphasis shifts away from
hard-coding a fixed set of behaviors towarddefining a smaller set of fundamental
behaviors that can be composedinto any number of more complex ones. Thus creating
objects withparticular behaviors requires more than simply instantiating a class.

(Design Pattern: Element of Reusable Object-Oriented Software)

## Issues and goals

**Having a ligtwave datamodel**, callable by all the code sections.
Twisted based development is /callback based/ therefore you need to
have preshared some generic way, that permit 

**Have a flexible design for extensions**: Notification, Delivery, Input,
Storage Database, Storage FileSystem, Receiver retriveral need to be implemented
as an abstract factory, that dispatch modules coherently with configuration or
runtime requests.

**Have a fixed functions as helper**, functions that manage the commonly used 
datatype of GLbackend (from the REST point of view, they are pointed out in
/Data object involved/)


