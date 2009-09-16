#!/usr/bin/env python
#
# Uses the GData API to post a document to Shareflow
#
##
from datetime import datetime
from optparse import OptionParser
from xml.utils import iso8601
import gdata.docs
import gdata.docs.service
import gdata.spreadsheet.service
import os.path
import pyshareflow
import sys
import tempfile

### CHANGE these to use your credentials ###
GOOGLE_LOGIN = '[GOOGLE LOGIN]'
GOOGLE_PWD = '[GOOGLE PASSWORD]'
GOOGLE_ACT_TYPE = '[HOSTED or GOOGLE]'

SHAREFLOW_LOGIN = '[EMAIL LOGIN]'
SHAREFLOW_PWD = '[SHAREFLOW PASSWORD]'
SHAREFLOW_DOMAIN = '[SHAREFLOW DOMAIN]'
### End ###

SOURCE = 'Shareflow-Examplev1'
EXTENSIONS = {'spreadsheet': 'xls',
              'document': 'doc',
              'presentation': 'ppt'}


# Parse command line options for doc and flow name
parser = OptionParser()
parser.add_option("-d", "--doc", dest="doc",
                  help="Find the Google Doc named NAME (required)", metavar="NAME")
parser.add_option("-f", "--flow", dest="flow",
                  help="Upload doc to the flow named NAME (required)", metavar="NAME")

(options, args) = parser.parse_args()

if not (options.doc and options.flow):
    parser.print_help()
    sys.exit(1)

# Setup the GData service
g_client = gdata.docs.service.DocsService()
g_client.ClientLogin(GOOGLE_LOGIN, GOOGLE_PWD, account_type=GOOGLE_ACT_TYPE, source=SOURCE)

query = gdata.docs.service.DocumentQuery()
query['title'] = options.doc
feed = g_client.Query(query.ToUri())

if feed.entry:
    entry = feed.entry[0]

    type = entry.GetDocumentType()

    # Get the relevant document attributes
    link = entry.GetAlternateLink().href
    timestamp = iso8601.parse(entry.updated.text)
    updated = datetime.fromtimestamp(timestamp).strftime("%b %m %Y, %I:%M %p")
    modified_by_name = entry.lastModifiedBy.name.text
    modified_by_email = entry.lastModifiedBy.email.text
    title = entry.title.text

    print "Found Google Doc: {0}".format(title)
    
    path = os.path.join(tempfile.gettempdir(), 
                        '{0}.{1}'.format(title.lower().replace(' ', '_'), 
                                         EXTENSIONS[type]))

    if type == 'spreadsheet':
        # Get an auth token for the spreadsheet service and swap if
        # for the one we currently use
        ss_client = gdata.spreadsheet.service.SpreadsheetsService()
        ss_client.ClientLogin(GOOGLE_LOGIN, GOOGLE_PWD, account_type=GOOGLE_ACT_TYPE, source=SOURCE)
        g_client.SetClientLoginToken(ss_client.GetClientLoginToken())

    g_client.Export(entry, path)

    try:
        # Get an API auth token from Shareflow
        shareflow_token = pyshareflow.Api.get_auth_token(SHAREFLOW_LOGIN, SHAREFLOW_PWD, SHAREFLOW_DOMAIN)
        shareflow = pyshareflow.Api(SHAREFLOW_DOMAIN, shareflow_token)

        msg = "{0} <{1}> updated the {2} '{3}' on {4}.\n\n"\
            "Click the link below to edit or view the attached revision.\n"\
            "{5}\n\n(posted via Shareflow API)\n".format(modified_by_name, 
                                                         modified_by_email,
                                                         type, title, updated, link)

        flow = shareflow.get_flow_by_name(options.flow)
        
        if flow:
            print "Uploading {0} to flow {1}".format(title, flow.name)
            shareflow.post_files(path, flow.id, comment=msg)
        else:
            sys.exit("Could not find a flow named {0}".format(options.flow))

    finally:
        os.remove(path)
    
else:
    sys.exit("Could not find a Google Doc named {0}".format(options.doc))

    
