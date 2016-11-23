.. _administrator_guide:

===================
Administrator Guide
===================

This chapter describes how to install, deploy, and administrate a c2cgeoportal
application.

The application administrator configures and administrates the application
through the database. The administrator does not deal with the files of the
application (the integrator is the one responsible for these files). Except for
one file (or set of files) actually: the MapServer mapfile. Adding layers to
the application indeed requires inserting information in the database, as well
as adding ``LAYER`` sections to the application's MapServer mapfile. So the
mapfile is a place where the administrator and the integrator collaborate.

Restriction - Hosts containing the word edit cause issues in the Admin interface on deleting elements:

This appears when trying to delete an element such as layer/layer group/theme/user/... from where the element can be edited (URL: .../admin/LayerV1/Layer#/edit). In this case all the words `edit` found in the URL get replaced with the word `delete` before the page is refreshed. If a host contains the word `edit` this is also replace and a wrong page redirect is made.

Alternatively it is possible to delete an element from the table view (URL: .../admin/LayerV1) where all elements of the type are shown. This can be done by deleting a selected row.

Content:

.. toctree::
   :maxdepth: 1

   mapfile
   administrate
   editing
   tinyows
