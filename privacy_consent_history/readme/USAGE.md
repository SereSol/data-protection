To record an answer collected by the office:

1.  Open a consent and change *Accepted*.
2.  The section *How it was collected* unlocks: choose the collection method,
    the collection date and, if needed, a note and attachments.
3.  Save: the consent is answered, the chatter shows how the answer was
    collected and the *Answer log* gets a new row.

The full log is in *Privacy \> Reports \> Consent Log*, the archive in
*Privacy \> Reports \> Consent Log Archive*.

Developers can call `res.partner._privacy_consent_log_archive()` to move the
log of a contact to the archive, for example before anonymizing it.
