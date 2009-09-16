# Google Docs Example with Shareflow #

This example uses the Google Docs
([gdata](http://code.google.com/apis/gdata/)) API to search for a
document with a given name, then upload the matching document to
Shareflow, along with a link to edit the document online.

Documents will be uploaded in the MS Office equivalent format,
i.e. documents are uploads as '.doc' files, Spreadsheets as '.xls'
files and Presentations as '.ppt' files.

## Usage ##

Make sure pyshareflow.py can be found in a directory in your
`PYTHONPATH`.

Edit the variables at the top of google\_docs\_example.py to reflect
your Google and your Shareflow credentials. In particular, edit:

* GOOGLE\_LOGIN: Your Google Docs login
* GOOGLE\_PWD: Your Google Docs password
* GOOGLE\_ACT\_TYPE: The account type: 'HOSTED'(Google Apps for your
  Domain) or 'GOOGLE' for regular accounts
* SHAREFLOW_LOGIN: Your Shareflow login email
* SHAREFLOW_PWD: Your Shareflow password
* SHAREFLOW_DOMAIN: Your login domain (i.e 'mycompany.zenbe.com')

### Running the example ###

After customizing as shown above, run the command as follows:

    python google_docs_example.py -f 'My Flow' -d 'My Google Doc'

This will search for a Google Doc called 'My Google Doc' and upload it
to a flow called 'My Flow'.

If the the flow or document does not exist, nothing will be uploaded.





