This module makes the consent log multi-company. It is a bridge between
*Privacy Consent History* and *Privacy Consent Multi Company*, installed
automatically when both are present:

- every row of the consent log belongs to the company of its data processing
  activity at the time the answer was recorded; the company is kept as
  evidence even if the activity is later moved to another company;
- archived rows keep the company of the log row they come from;
- users only see the log and archive rows of the companies selected in the
  company switcher. Rows archived before this module was installed have no
  company and are visible in every company.
