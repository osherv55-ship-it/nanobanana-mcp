// Clinic (גלונס אסתטיקה) mailbox variant — all invoices/receipts.
// Run INSIDE the clinic's Google account (script.google.com):
//   1. New project → paste this file → save
//   2. Run setup() once → approve consent (folder is created and shared automatically)
//   3. Run saveInvoices() once (function dropdown next to Run!) — 90-day backfill
//   4. Run setupDailyTrigger() once → hands-free forever
// Files named "<gmailMessageId>_body.html" / "<gmailMessageId>_<attachment>".

const SHARE_WITH = 'osherv55@gmail.com';
const PROP = PropertiesService.getScriptProperties();
const SEARCH = '(חשבונית OR קבלה OR invoice OR receipt OR from:business-updates.facebook.com) newer_than:90d';
const TIME_LIMIT_MS = 270000;

function setup() {
  const folder = DriveApp.createFolder('חשבוניות קליניקה 📥');
  folder.addEditor(SHARE_WITH);
  PROP.setProperty('FOLDER_ID', folder.getId());
  console.log('FOLDER_ID: ' + folder.getId());
}

function saveInvoices() {
  const start = Date.now();
  const folder = DriveApp.getFolderById(PROP.getProperty('FOLDER_ID'));
  const existing = new Set();
  const it = folder.getFiles();
  while (it.hasNext()) existing.add(it.next().getName());

  for (const thread of GmailApp.search(SEARCH, 0, 500)) {
    if (Date.now() - start > TIME_LIMIT_MS) {
      ScriptApp.newTrigger('saveInvoices').timeBased().after(60000).create();
      console.log('time limit - auto-continuing in 1 minute');
      return;
    }
    for (const msg of thread.getMessages()) {
      const id = msg.getId();
      try {
        const bodyName = id + '_body.html';
        if (!existing.has(bodyName)) {
          const html = '<!-- subject: ' + msg.getSubject() + ' | from: ' + msg.getFrom() +
                       ' | date: ' + msg.getDate() + ' -->\n' + msg.getBody();
          folder.createFile(Utilities.newBlob(html, 'text/html', bodyName));
          existing.add(bodyName);
        }
        for (const att of msg.getAttachments({ includeInlineImages: false })) {
          try {
            const fname = att.getName() || '';
            if (!/\.(pdf|jpe?g|png)$/i.test(fname)) continue;
            const name = id + '_' + fname.replace(/[\/\\:*?"<>|]/g, '_').slice(0, 100);
            if (existing.has(name)) continue;
            folder.createFile(att.copyBlob().setName(name));
            existing.add(name);
          } catch (e) { console.log('skipped att: ' + id + ' - ' + e); }
        }
      } catch (e) { console.log('skipped msg: ' + id + ' - ' + e); }
    }
  }
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === 'saveInvoices') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('saveInvoices').timeBased().everyDays(1).atHour(6).create();
  console.log('done - daily trigger re-armed');
}

function setupDailyTrigger() {
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('saveInvoices').timeBased().everyDays(1).atHour(6).create();
}
