// AAA mailbox variant — run this INSIDE the AAA Google account (script.google.com).
// Creates its own Drive folder, shares it with osherv55@gmail.com, and syncs
// every invoice email: attachments AND the email body itself (as .html), so
// body-only receipts are captured too.
//
// One-time setup, logged in as the AAA account:
//   1. script.google.com → New project → paste this file → save
//   2. Run setup() once → approve consent → check the log for FOLDER_ID
//   3. Run saveInvoices() once (first backfill, last 90 days)
//   4. Run setupDailyTrigger() once → done forever
//
// Files are named "<gmailMessageId>_<name>" for ledger matching.

const SHARE_WITH = 'osherv55@gmail.com';
const PROP = PropertiesService.getScriptProperties();

function setup() {
  const folder = DriveApp.createFolder('חשבוניות AAA 📥');
  folder.addEditor(SHARE_WITH);
  PROP.setProperty('FOLDER_ID', folder.getId());
  console.log('FOLDER_ID: ' + folder.getId());
}

function saveInvoices() {
  const folder = DriveApp.getFolderById(PROP.getProperty('FOLDER_ID'));
  const existing = new Set();
  const it = folder.getFiles();
  while (it.hasNext()) existing.add(it.next().getName());

  const query = '(חשבונית OR קבלה OR invoice OR receipt) newer_than:90d';
  for (const thread of GmailApp.search(query, 0, 400)) {
    for (const msg of thread.getMessages()) {
      const id = msg.getId();
      try {
        // 1. attachments
        for (const att of msg.getAttachments({ includeInlineImages: true })) {
          try {
            const type = att.getContentType() || '';
            const fname = att.getName() || '';
            if (!/pdf|jpe?g|png/i.test(type) && !/\.(pdf|jpe?g|png)$/i.test(fname)) continue;
            if (!att.getSize || att.getSize() === 0) continue;
            const safe = fname.replace(/[\/\\:*?"<>|]/g, '_').slice(0, 100) || 'file.pdf';
            const name = id + '_' + safe;
            if (existing.has(name)) continue;
            const blob = att.copyBlob();
            blob.setName(name);
            folder.createFile(blob);
            existing.add(name);
          } catch (e) { console.log('skipped att: ' + id + ' - ' + e); }
        }
        // 2. message body (covers body-only receipts like Wolt/Stripe)
        const bodyName = id + '_body.html';
        if (!existing.has(bodyName)) {
          const html = '<!-- subject: ' + msg.getSubject() + ' | from: ' + msg.getFrom() +
                       ' | date: ' + msg.getDate() + ' -->\n' + msg.getBody();
          folder.createFile(Utilities.newBlob(html, 'text/html', bodyName));
          existing.add(bodyName);
        }
      } catch (e) { console.log('skipped msg: ' + id + ' - ' + e); }
    }
  }
}

function setupDailyTrigger() {
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('saveInvoices').timeBased().everyDays(1).atHour(6).create();
}
