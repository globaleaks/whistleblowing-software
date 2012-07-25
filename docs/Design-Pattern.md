
## GLBackend design

_Creational pattern instead of inheritance based pattern_

Creational patterns become important as systems evolve to depend moreon object
composition than class inheritance. As that happens,emphasis shifts away from
hard-coding a fixed set of behaviors towarddefining a smaller set of fundamental
behaviors that can be composedinto any number of more complex ones. Thus creating
objects withparticular behaviors requires more than simply instantiating a class.

(Design Pattern: Element of Reusable Object-Oriented Software)

## Issues and goals

**Have a ligtwave datamodel**, callable by all the code sections, this is 
a series of Storm extensions that handle ORM interaction.

**Have a flexible design for extensions**: Notification, Delivery, Input,
Storage Database, Storage FileSystem, Receiver retriveral need to be implemented
as an abstract factory, that dispatch modules coherently with configuration or
runtime requests. 
All the module use Creational pattern inside.

**Have a set of helper functions**, functions that manage the commonly used 
datatype of GLbackend. 
Are implemented in globaleaks/utils/ code, use inheritance based pattern.
