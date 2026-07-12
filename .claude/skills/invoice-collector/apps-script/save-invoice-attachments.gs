// Auto-sync Gmail invoice attachments + email bodies to the Drive folder
// "חשבוניות למעקב 📥". v3: 90-day window, explicit attachment flags,
// per-message body.html capture, hyp.co.il debug logging.
// Setup: paste at script.google.com, run saveInvoiceAttachments once (approve),
// then run setupDailyTrigger once.

const FOLDER_ID = '1-EdHr7QezErSBkOiX83d5Yx7JQ9O_CE5';
const SEARCH = '(חשבונית OR קבלה OR invoice OR receipt) newer_than:90d';

function saveInvoiceAttachments() {
  const folder = DriveApp.getFolderById(FOLDER_ID);
  const existing = new Set();
  const it = folder.getFiles();
  while (it.hasNext()) existing.add(it.next().getName());

  for (const thread of GmailApp.search(SEARCH, 0, 500)) {
    for (const msg of thread.getMessages()) {
      const id = msg.getId();
      try {
        const atts = msg.getAttachments({ includeInlineImages: true, includeAttachments: true });
        if (msg.getFrom().indexOf('hyp.co.il') > -1) {
          console.log('hyp msg ' + id + ': ' + atts.length + ' attachments: ' +
            atts.map(a => a.getName() + '|' + a.getContentType()).join(', '));
        }
        for (const att of atts) {
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
  ScriptApp.newTrigger('saveInvoiceAttachments').timeBased().everyDays(1).atHour(6).create();
}
