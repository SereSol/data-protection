This module makes data processing activities multi-company, for databases
where each company is a separate data controller:

- every activity belongs to exactly one company;
- the controller of an activity is the contact of its company, read-only in
  the form view;
- users only see the activities of the companies selected in the company
  switcher;
- each company can set a privacy email, the address for data protection
  matters that other privacy modules can use as sender and contact.

Consents are made multi-company by a separate bridge module.
