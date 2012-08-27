# Node
*Unique Instance*

## Attributes

 * **Contexts**
 This defines what are the possible contexts for a submission that are enabled
 on the current GL Node (e.x. Corruption, Money Laundering, Corporate
 Malpractice).

 * **Groups**
 Specifies the list of groups that can be selected as receivers of the
 submission.

 * **Statistics**
 Provides statistics related to node usage (e.x. how many submission have been
 made through the a certain node, how many tips have been viewed, etc.)

 * **Properties**
 What security and misc properties the Node has. This includes are the targets
 selected by the node admin or have they requested to be in the list, is
 anonymity enforced, are the receivers part of the administration of the node,
 is end-to-end encryption enforced.

 * **Description**
 The description of the Node to be displayed on Leak Directory

 * **Name**
 The name of the Node to be displayed on leakdirectory.

 * **public_site**
 The address of the public website of the Whistleblowing intitiative

 * **hidden_service**
 The address of the Tor hidden service of the node.

 * **fields**
 What fields are supported in the submission for every available submission
 context.

# Submission
*Single Instance*

## Methods

 * **create**
 Creates a new submission and returns a temporary submission ID.

 * **add_material**
 Adds material to the specified submission ID

 * **submit_fields**
 Submit the submission fields to the temporary submission ID specified.

 * **add_group**
 Add the submission to the specified receiver group

 * **finalize**
 Complete the submission

# Tip
*Mutliple Instaces*

## Attributes

 * **id**
 Internal ID of the Tip

 * **address**
 The unique address of the Tip

 * **password**
 (optional) password to restrict access to the Tip

## Methods

 * add_comment
 Adds a comment to the Tip.


# Receiver Tip
*Multiple Instance*

## Attributes

 * **total_view_count**
 The number of total views of this specific unique Tip

 * **total_download_count**
 How many times the owner of this unique Tip has downloaded the material

 * **relative_view_count**
 Number of views since last reset (when a comment or material is added the
 relative counter is decreased)

 * **relative_download_count**
 Number of downloads since last reset

## Method

 * **download_material(id)**
 Download the material for this Tip. The ID is used to specify what material
 pack should be downloaded (i.e. The full one, or just one of the newly added
 ones)

 * **pertinence**
 Express a vote on pertinence of this Tip

 * **increment_visit**
 Increment the visit counter of this Tip for this receiver

 * **increment_download**
 Increment the download counter

 * **delete_tulip**
 If the receiver has delete permission, delete this Tip.

# Whistleblower Tip
*Single Instance*

## Methods

 * **add_material**
 Add a new material to the Tip

# Internal Tip
*Single Instance*

## Attributes

 * **id**
 Internal ID of the Tip

 * **fields**
 The fields of the submission.

 * **material**
 The list of materials associated with a particular submission.

 * **pertinence**
 How much pertinent this submission is with the node

 * **expiration_time**
 When the Tip should expire.


# Task
*Multiple Instances*

This represents a notification or delivery task that should be inserted
into the task manager queue.

## Attributes

 * **receiver**
 Who is the recipient of this task.

 * **type**
 Notification or Delivery

## Methods

 * **spam_check()**
 Performs anti-spam checks on the notification to be send to the receiver

 * **handle()**
 Handles the notification or delivery of the Task


# Receiver
*Multiple Instance*

## Attributes
 * **PublicName**
 The name of the receiver to be displayed publicly

 * **PrivateName**
 Internal name of the receiver, only visible to the node administrator

 * **Description**
 Description of the receiver, can be public or private.

 * **NotificationMethod**
 What method should be used for notification (e.x. Email, Ticketing system,
 HTTP request, etc.)

 * **DeliveryMethod**
 What should be used for the delivery of the submission and/or material (e.x.
 Email, ssh server, ftp server, etc.)

## Methods
 * **notify_and_delivery()**
 Execute the notifcation and delivery actions for this receiver.


