# -*- coding: utf-8 -*-

from os import path

from gluon import current
from gluon.html import *
from gluon.validators import IS_NULL_OR
from gluon.storage import Storage

from s3.s3crud import S3CRUD
from s3.s3search import S3DateFilter, S3OptionsFilter, S3TextFilter
from s3.s3utils import s3_auth_user_represent_name, s3_avatar_represent, s3_unicode
from s3.s3validators import IS_LOCATION
from s3.s3widgets import S3LocationAutocompleteWidget

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
class datalist_dl_post():
    """ AJAX URL for CMS Posts (for Homepage) """

    def __call__(self):

        return homepage()

# =============================================================================
def homepage():
    """
        Custom Homepage
        - DataList of CMS Posts
    """

    if not current.auth.is_logged_in():
        return login()

    T = current.T
    s3db = current.s3db
    request = current.request
    response = current.response
    s3 = response.s3

    table = s3db.cms_post

    field = table.series_id
    field.label = T("Type")
    field.readable = field.writable = True
    field.requires = field.requires.other
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
    field = table.location_id
    field.represent = location_represent
    field.requires = IS_NULL_OR(IS_LOCATION(level="L3"))
    field.widget = S3LocationAutocompleteWidget(level="L3")
    table.created_by.represent = s3_auth_user_represent_name
    field = table.body
    field.label = T("Text")
    field.widget = None
    table.comments.readable = table.comments.writable = False

    # Return to List view after create
    url_next = URL(f="index", args=None)

    list_layout = render_homepage_posts

    list_fields = ["series_id",
                   "location_id",
                   "created_on",
                   "body",
                   "created_by",
                   "created_by$organisation_id",
                   "document.file",
                   ]

    filter_widgets = [S3TextFilter(["body"],
                                   label="",
                                   _class="filter-search",
                                   _placeholder=T("Search").upper()),
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
                   filter_formstyle = filter_formstyle,
                   filter_submit = (T("Filter Results"), "btn btn-primary"),
                   filter_widgets = filter_widgets,
                   list_layout = list_layout,
                   )

    s3.dl_pagelength = 5

    if "datalist_dl_post" in request.args:
        ajax = True
    else:
        ajax = False

    def prep(r):
        if ajax:
            r.representation = "dl"
        return True
    s3.prep = prep

    crud_settings = s3.crud
    crud_settings.formstyle = "bootstrap"
    crud_settings.submit_button = T("Save changes")
    # Done already within Bootstrap formstyle (& anyway fails with this formstyle)
    #crud_settings.submit_style = "btn btn-primary"
    
    request.args = ["datalist"]
    output = current.rest_controller("cms", "post",
                                     list_ajaxurl = URL(f="index", args="datalist_dl_post"))

    if ajax:
        response.view = "plain.html"
    else:
        form = output["form"]
        # Remove duplicate Submit button
        form[0][-1] = ""
        if form.errors:
            s3.jquery_ready.append('''$("#myModal").modal("show")''')
        # Set Title & View after REST Controller, in order to override
        output["title"] = response.title = current.deployment_settings.get_system_name()
        view = path.join(request.folder, "private", "templates",
                         "TLDRMP", "views", "index.html")
        try:
            # Pass view as file not str to work in compiled mode
            response.view = open(view, "rb")
        except IOError:
            from gluon.http import HTTP
            raise HTTP("404", "Unable to open Custom View: %s" % view)

        # Latest 5 Disasters
        resource = s3db.resource("event_event")
        list_fields = ["name",
                       "zero_hour",
                       "closed",
                       ]
        datalist, numrows, ids = resource.datalist(fields=list_fields,
                                                   start=None,
                                                   limit=5,
                                                   listid="event_datalist",
                                                   layout=render_homepage_events)
        if numrows == 0:
            # Empty table or just no match?

            table = resource.table
            if "deleted" in table:
                available_records = current.db(table.deleted != True)
            else:
                available_records = current.db(table._id > 0)
            if available_records.select(table._id,
                                        limitby=(0, 1)).first():
                msg = DIV(S3CRUD.crud_string(resource.tablename,
                                             "msg_no_match"),
                          _class="empty")
            else:
                msg = DIV(S3CRUD.crud_string(resource.tablename,
                                            "msg_list_empty"),
                          _class="empty")
            data = msg

        else:
            # Render the list
            dl = datalist.html()
            data = dl

        output["disasters"] = data

    return output

# -----------------------------------------------------------------------------
def login():
    """
        Custom Login page
    """

    response = current.response
    request = current.request

    view = path.join(request.folder, "private", "templates",
                     "TLDRMP", "views", "login.html")
    try:
        # Pass view as file not str to work in compiled mode
        response.view = open(view, "rb")
    except IOError:
        from gluon.http import HTTP
        raise HTTP("404", "Unable to open Custom View: %s" % view)

    response.title = current.T("Login")

    request.args = ["login"]
    auth = current.auth
    auth.settings.formstyle = "bootstrap"
    login = auth()

    return dict(
        form = login
    )

# -----------------------------------------------------------------------------
def filter_formstyle(row_id, label, widget, comment):
    """
        Custom Formstyle for FilterForm

        @param row_id: HTML id for the row
        @param label: the label
        @param widget: the form widget
        @param comment: the comment
    """

    if label:
        return DIV(TR(label),
                   TR(widget))
    else:
        return widget

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

    represent = "%s | %s | %s" % (s3_unicode(row.L1).upper() if row.L1 else "",
                                  s3_unicode(row.L2).upper() if row.L2 else "",
                                  s3_unicode(row.L3).upper() if row.L3 else "",
                                  )
    return represent

# -----------------------------------------------------------------------------
def render_homepage_posts(rfields, record, **attr):
    """
        Custom dataList item renderer for CMS Posts on the Homepage

        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """
    
    pkey = "cms_post.id"

    # Construct the item ID
    listid = "datalist"
    if pkey in record:
        item_id = "%s-%s" % (listid, record[pkey])
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    raw = record._row
    series = record["cms_post.series_id"]
    date = record["cms_post.created_on"]
    body = record["cms_post.body"]
    location = record["cms_post.location_id"]
    location_id = raw["cms_post.location_id"]
    location_url = URL(c="gis", f="location", args=[location_id])
    author = record["cms_post.created_by"]
    author_id = raw["cms_post.created_by"]
    organisation = record["auth_user.organisation_id"]
    organisation_id = raw["auth_user.organisation_id"]
    org_url = URL(c="org", f="organisation", args=[organisation_id])
    # @ToDo: Optimise by not doing DB lookups (especially duplicate) within render, but doing these in the bulk query
    avatar = s3_avatar_represent(author_id,
                                 _class="media-object",
                                 _style="width:50px;padding:5px;padding-top:0px;")
    s3db = current.s3db
    ptable = s3db.pr_person
    ltable = s3db.pr_person_user
    query = (ltable.user_id == author_id) & \
            (ltable.pe_id == ptable.pe_id)
    row = current.db(query).select(ptable.id,
                                   limitby=(0, 1)
                                   ).first()
    if row:
        avatar_url = URL(c="hrm", f="person", args=[row.id])
    else:
        avatar_url = "#"
    avatar = A(avatar,
               _href=avatar_url,
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

# -----------------------------------------------------------------------------
def render_homepage_events(rfields, record, **attr):
    """
        Custom dataList item renderer for Events on the Homepage

        @param rfields: the S3ResourceFields to render
        @param record: the record as dict
        @param attr: additional HTML attributes for the item
    """

    pkey = "event_event.id"

    # Construct the item ID
    listid = "event_datalist"
    if pkey in record:
        item_id = "%s-%s" % (listid, record[pkey])
    else:
        # template
        item_id = "%s-[id]" % listid

    item_class = "thumbnail"

    raw = record._row
    record_id = raw["event_event.id"]
    name = record["event_event.name"]
    date = record["event_event.zero_hour"]
    closed = raw["event_event.closed"]

    if closed:
        edit_bar = DIV()
    else:
        item_class = "%s disaster" % item_class

        # @ToDo: Check Permissions
        edit_bar = DIV(A(I(" ",
                           _class="icon icon-edit",
                           ),
                         _href=URL(c="event", f="event", args=[record_id]),
                         ),
                       A(I(" ",
                           _class="icon icon-remove-sign",
                           ),
                         _href=URL(c="event", f="event",
                                   args=[record_id, "delete"]),
                         ),
                       _class="edit-bar fright",
                       )

    # Render the item
    item = DIV(edit_bar,
               H5(name),
               SPAN(date,
                    _class="date-title",
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
