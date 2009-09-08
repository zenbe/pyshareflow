# Python library for Zenbe Shareflow API (v2) #

## Overview ##

This is a simple python library to interface with Zenbe's Shareflow
service.

The library was coded against Python 2.6.2.

Currently pyshareflow requires an API key. An API key can be obtained by
sending a request to Zenbe via our [contact
form](http://zenbe.com/contact).

An API key is scoped to a user. This means that a user of this API
only sees the flows and content they have access to. It also means
that any posts or comments made via the API show up in the web
interface with the user as the author.

## Operations ##

### Creating an API instance ###

    >>> import pyshareflow
    >>>	api = pyshareflow.Api('biz.zenbe.com', 'yourdomain.zenbe.com', 'your key')

### Retrieving Flows ###

    >>> flows = api.get_flows()

Retrieves an array of Flow objects, ordered by created at time. There
is a default limit of 30 flows, and a max limit of 100 flows.

    >>> flows = api.get_flows(limit=100, order_by='created')

Returns up to 100 flows, ordered by when the flow was last updated.

    >>> flows = api.get_flows(name='My Shareflow')
    >>> flows[0].name
    'My Shareflow'

Returns a list of all flows matching a particular name.

#### Flow attributes ####

* `id`: The UUID of the flow
* `name`: The flow name
* `email_address`: The email address of the flow. Emails sent here show
  up on the flow
* `created_at`: A `datetime` object representing the flow creation time
* `updated_at`: A `datetime` object representing the flow update time
* `is_default`: A `boolean` indicating if the flow is your team's
  default flow
* `owner_name`: The creator of the flow
* `quota_percentage`: A `float` indicating the percentage of total
  storage space used by this flow.
* `quota_count`: An `int` representing the bytes used by this flow
* `rss_url`: The URL containing the RSS feed for this flow.
* `users`: A list of `User` objects representing who has accepted an
  invitation to this flow. See the description of `User` below.
* `invitations`: A list of `Invitation` objects representing users who
  have not yet accepted an invitation to the flow
* `owner`: A `User` object representing the owner of the flow

_Note_: Posts are not attached to flows. The are retrieved separately
as described below.

#### User attributes ####

* `id`: An `int` id of the user
* `login`: The login name of the user. Typically the same as the email
  address.
* `first_name`: The first name
* `last_name`: The last name
* `email`: The user's email address
* `avatar_url`: The url to fetch the user's avatar
* `is_online`: A `boolean` indicating if the user is logged in right
  now
* `time_zone`: The time zone string for the user

  
#### Invitation attributes ####

* `id`: The uuid of the invitation
* `Email`: The email address for the invitation

### Creating flows ###

    >>> new_flow = api.create_flow('My New Flow')

### Modifying flows ###

    >>> updated_flow = api.update_flow_name('New Flow Name', 'flow_id')

Renames the flow with the given flow id and returns the new flow
object.

    >>> api.create_invitations('flow id', 'bob@example.com')

Invites a user to the flow. This sends an invitation email to the
user.

    >>> api.create_invitations('flow id', ['bob@example.com', sue@example.com'])

Invites all the email addresses specified in the array to the flow.

    >>> api.create_invitations('flow id', "Bob Smith <bob@example.com>")

An invitation using an RFC2822 compliant email address.

    >>> api.delete_invitations('flow id', 'bob@example.com')

Deletes an invited user from a flow. The array syntax may also be used
to uninvite multiple invitees.

### Deleting flows ###

    >>> api.delete_flow('flow id')

Deletes a flow. _Be careful!_ All data will be deleted.

### Retrieving Posts ###

    >>> api.get_posts()

Retrieves the latest 30 posts across all flows, sorted by created at
time.

    >>> api.get_posts(limit=100, flow_id='flow id', order_by='updated)

Gets at most 100 posts for the given flow id, ordered by updated time.

    >>> api.get_posts(flow_id='flow id', include_comments=False, order_by='updated')

Gets the most recently updated 30 posts across flows, but excludes
comments.

    >>> api.get_posts(before=datetimeobj)

Gets the 30 posts created before the given `datetime` object.

    >>> api.get_posts(after=datetimeobj, order_by='updated')

Gets any posts updated after the given `datetime` object. This query
is useful for checking for new activity.

    >>> api.get_posts(before=begin, after=end)

Gets the posts in between the two dates. This is an exclusive
operation.

    >>> api.get_posts(search_term='presentation')

Gets any posts matching the term 'presentation'. Will also search
comments, unless `include_comments=False`.

    >>> api.get_posts(flow_id='flow id', search_term='presentation')

Executes the preceding search, but restricts it to a particular flow.

_Note_: For convenience there is also an `api.search(search_term)`
method.

#### Post attributes ####

There are a few different post sub-types. These are the attributes
common to all posts.

* `id`: The post uuid
* `flow_id`: The id of the flow the post is part of
* `flow_name`: The name of the flow the post is part of
* `post_type`: A string describing the type of post
* `content`: The post content. May be empty for some post types
* `star`: The star indicator
* `created_at`: A `datetime` object representing when the post was created
* `updated_at`: A `datetime` object representing when the post was updated
* `reply_ids`: A `set` of ids of comments that are replies to this post
* `file_ids`: A `set` of ids of files associated with this post
* `user_id`: The id of the user responsible for this post
* `files`: A `list` of `File` objects associated with this post
* `comments`: A `list` of `Comment` objects associated with this post
* `user`: A `User` object representing the user responsible for this post
  

#### Post Subtypes ####

There are a few subtypes of a `Post`:

##### MapPost #####

Returned when a map was posted.

* `get_address()`: Returns the address of the map as a string.
* `get_coordinates()`: Returns the latitude and longitude coordinates as
  a tuple.
  

##### FilePost #####

This is the type of post for any post containing files.

##### ImagePost #####

Indicates images are attached to this post. The corresponding `File`
objects will include dimension information as well as a URL to the
image thumbnail.

An ImagePost may also represent a link to an image on an external
service (Flickr for example). In that case, there may be no associated
files. To deal with this case:

    >>> if image_post.is_embed():
    ...    print image_post.get_external_link()
    ...
    http://www.flicker.com/foo

##### VideoPost #####

Indicates videos are attached to this post. This may also represent a
video linked to on an external service (like YouTube or Hulu). In that
case, use the `get_external_link()` method in the `ImagePost` example
to get the link to the video content.

##### HTMLPost #####

Indicates the `content` field of the post is HTML.

##### EmailPost #####

Indicates the post is an email. This type of post has a `msg`
attribute, which points to a `File` object representing the message.

The following methods are also available:

* `get_sender()`: Returns the display name of the sender.
* `get_subject()`: Returns the subject of the message.
* `get_summary()`: Returns a 255 character preview of the message.
* `get_msg_content()`: Downloads the full content of the message.
  

##### EventPost #####

Indicates the post is an event. This type of post has a `event`
attribute, which points to a `File` object representing the ICS
representation of the event.

The following methods are also available:

* `get_ics_content()`: Returns the ICS representation of the event
  

#### Detecing Post Types ####

You can use `isinstance()` to detect post types. For convenience, all
posts implement the following methods, which return a `boolean`:

* `is_map()`
* `is_email()`
* `is_event()`
* `is_file()`
* `is_image()`
* `is_video()`
* `is_html()`
* `is_event()`
  

#### File attributes ####

The following are attributes of `File` objects:

* `id`: The uuid of the file
* `file_name`: The name of the file
* `file_size`: The size (in bytes) of the file
* `post_id`: The uuid of the post this file is associated with
* `content_type`: The content type of the file
* `is_image`: Whether or not the file is an image
* `meta_data`: Metadata about the file. Only emails and event files have
  metadata.
* `width`: The width of the file (if it's an image)
* `height`: The height of the file (if it's an image)
* `thumbnail_url`: A thumbnail of the file. Usually only valid for
  images, but some documents may have thumbnails of their cover sheets
  as well.
* `created_at`: A `datetime` object representing when this file was created.
* `updated_at`: A `datetime` object representing when this file was updated.
* `url`: The URL this file can be retrieved from

Methods:

* `retrieve()`: Returns the retrieved file content.
  

#### Comment attributes ####

Comments are associated with `Post` objects. They have the following
attributes:

* `id`: The uuid of the comment
* `flow_id`: The id of the flow this comment is associated with
* `flow_name`: The name of the flow the comment is associated with
* `reply_to`: The post id this comment is a reply to
* `content`: The content of the comment
* `created_at`: A `datetime` object representing the creation time
* `updated_at`: A `datetime` object representing the update time
* `user_id`: The id of the user associated with this comment
* `user`: The `User` object of the user associated with this comment
* `post`: The `Post` this comment is in reply to

### Modifying Posts ###

    >>> api.update_post('post_id', 'New post content.')

Updates the post with the given id with the new content. Returns the
updated `Post` object.

    >>> api.create_comment('post_id', 'This is a comment.')

Creates a comment associated with the post with the given id.

    >>> api.delete_comment('comment_id')

Deletes the comment with the given id.

### Deleting Posts ###

    >>> api.delete_post('post id')

Permanently deletes the post (and any associated files and comments)
with the given id.

## Exceptions ##

Any API method may throw an `HTTPException` when there are
HTTP-related errors.

There are 3 special exceptions:

### ResourceException ###

This is thrown if you are over-quota or are attempting to invite too
many users.

### InvalidRequest ###

This is thrown if you specify an invalid query, or try to modify an
read-only attribute.

### ServiceError ###

This happens when there is an internal server error (HTTP code 500) on
our part.

## TODO ##

* Add offset, before, after params to get_flows
* Implement offset for posts
* Implement file uploads
* Implement removing a user (not invitee) from a flow
* Implement a streaming file retrieve() operation
* Implement permaline attribute for Flows, Posts, Comments
* __str__ method for Post
* Offset support
* Add operation to post events
* Docstrings
* Unit tests

