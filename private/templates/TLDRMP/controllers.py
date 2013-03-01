# -*- coding: utf-8 -*-

from os import path

from gluon import current
from gluon.html import *
from gluon.storage import Storage

from s3 import S3DateFilter, S3OptionsFilter, S3TextFilter

# =============================================================================
class index():
    """ Custom Home Page """

    def __call__(self):

        return homepage()

# =============================================================================
class datalist():
    """ Alternate URL for homepage """

    def __call__(self):

        return homepage()

# =============================================================================
def homepage():
    """
        Custom Homepage
        - DataList of CMS Posts
    """

    T = current.T
    s3db = current.s3db
    request = current.request
    response = current.response

    table = s3db.cms_post

    field = table.name
    field.readable = field.writable = False
    field = table.title
    field.readable = field.writable = False
    field = table.avatar
    field.default = True
    field.readable = field.writable = False
    field = table.replies
    field.default = False
    field.readable = field.writable = False
    table.location_id.represent = location_represent

    # Return to List view after create
    url_next = URL(f="index", args=None)

    list_layout = render

    list_fields = ["series_id",
                   "location_id",
                   "created_on",
                   "body",
                   "created_by",
                   "created_by$organisation_id",
                   "document.file",
                   ]

    filter_widgets = [S3TextFilter(["body"],
                                   label=""),
                      S3OptionsFilter("location_id",
                                      label=T("Filter by Location"),
                                      represent="%(name)s",
                                      cols=3),
                      S3OptionsFilter("created_by$organisation_id",
                                      label=T("Filter by Organization"),
                                      represent="%(name)s",
                                      cols=3),
                      S3DateFilter("created_on",
                                   label=T("Filter by Date")),
                      ]

    s3db.configure("cms_post",
                   create_next = url_next,
                   update_next = url_next,
                   list_fields = list_fields,
                   filter_widgets = filter_widgets,
                   list_layout = list_layout,
                   )

    request.args = ["datalist"]
    output = current.rest_controller("cms", "post")
    
    response.title = current.deployment_settings.get_system_name()
    view = path.join(request.folder, "private", "templates",
                     "TLDRMP", "views", "index.html")
    try:
        # Pass view as file not str to work in compiled mode
        response.view = open(view, "rb")
    except IOError:
        from gluon.http import HTTP
        raise HTTP("404", "Unable to open Custom View: %s" % view)

    # @ToDo: Latest 5 Disasters
    #output["disasters"] = disasters

    return output

# -----------------------------------------------------------------------------
def location_represent(id, row=None):
    """
        Custom Representation of Locations
    """

    if not row:
        if not id:
            return current.messages["NONE"]
        table = current.s3db.gis_location
        row = current.db(table.id == id).select(table.L1,
                                                table.L2,
                                                table.L3,
                                                limitby=(0, 1)).first()

    represent = "%s | %s | %s" % (row.L1.upper() if row.L1 else "",
                                  row.L2.upper() if row.L2 else "",
                                  row.L3.upper() if row.L3 else "",
                                  )
    return represent

# -----------------------------------------------------------------------------
def render(rfields, record, **attr):
    """
        Custom dataList item renderer

        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """
    
    #pkey = str(self.resource._id)
    pkey = "cms_post.id"

    # Construct the item ID
    #listid = self.listid
    listid = "datalist"
    if pkey in record:
        item_id = "%s-%s" % (listid, record[pkey])
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    series = record["cms_post.series_id"]
    date = record["cms_post.created_on"]
    body = record["cms_post.body"]
    location = record["cms_post.location_id"]
    location_url = URL(c="gis", f="location",
                       #args=[location_id]
                       )
    author = record["cms_post.created_by"]
    organisation = record["auth_user.organisation_id"]
    org_url = URL(c="org", f="organisation",
                  #args=[org_id]
                  )
    avatar = "http://www.gravatar.com/avatar/00000000000000000000000000000000?d=mm"
    avatar = A(IMG(_src=avatar,
                   _class="media-object",
                   _style="width:50px;padding:5px;padding-top:0px;",
                   ),
               _href="#",
               _class="pull-left",
               )
    # @ToDo: Check Permissions
    edit_bar = DIV(I(" ",
                     _class="icon icon-edit",
                     ),
                   I(" ",
                     _class="icon icon-remove-sign",
                     ),
                   _class="edit-bar fright",
                   )
    #document = record["doc_document.file"]
    #if document:
    doc_url = URL(c="default", f="download",
                  #args=[document]
                  )
    doc_link = A(I(_class="icon icon-paper-clip fright"),
                 _href=doc_url)
                 

    if series == "Alert":
        item_class = "%s disaster" % item_class

    # Render the item
    item = DIV(DIV(I(SPAN(" %s" % current.T(series),
                          _class="card-title",
                          ),
                     _class="icon icon-%s" % series.lower(),
                     ),
                   SPAN(A(location,
                          _href=location_url,
                          ),
                        _class="location-title",
                        ),
                   SPAN(date,
                        _class="date-title",
                        ),
                   edit_bar,
                   _class="card-header",
                   ),
               DIV(avatar,
                   DIV(DIV(body,
                           DIV("%s - " % author,
                               A(organisation,
                                 _href=org_url,
                                 _class="card-organisation",
                                 ),
                               doc_link,
                               _class="card-person",
                               ),
                           _class="media",
                           ),
                       _class="media-body",
                       ),
                   _class="media",
                   ),
               _class=item_class,
               _id=item_id,
               )

    return item

# =============================================================================
class secondary():
    """ Custom Navigation """

    def __call__(self):

        view = path.join(current.request.folder, "private", "templates",
                         "TLDRMP", "views", "secondary.html")
        try:
            # Pass view as file not str to work in compiled mode
            current.response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        return dict()

# END =========================================================================
