This module keeps evidence of every consent answer:

- a log row for each answer, with date and time of the server, IP address,
  browser, who filled it in and as whom (data subject, parent, legal guardian,
  employee), source (back office, email link, import) and an optional related
  document;
- when an employee changes the acceptance of a consent in the back office, the
  consent becomes *Answered* and the employee must say how and when the answer
  was collected (configurable collection methods, collection date, note and
  attachments, posted in the chatter);
- the log cannot be changed or deleted by users;
- an archive keeps a copy of the log detached from the contact, for example
  before the contact is anonymized, and deletes it automatically after the
  retention period set in the settings.

Other modules can extend the sources and roles of the log and confirm answers
given on a page only when the page is submitted.
