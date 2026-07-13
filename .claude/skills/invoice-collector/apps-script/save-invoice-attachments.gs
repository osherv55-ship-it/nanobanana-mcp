// Auto-sync Gmail invoice attachments + email bodies to the Drive folder
// "חשבוניות למעקב 📥". v4: self-resuming (no 6-min timeout failures),
// Gmail-API fallback for attachments GmailApp can't see (e.g. hyp.co.il),
// re-arms its own daily trigger on completion.
// Setup: enable the Gmail API advanced service (Services + -> Gmail API -> Add),
// paste, run saveInvoiceAttachments once. It continues itself until done.

const FOLDER_ID = '1-EdHr7QezErSBkOiX83d5Yx7JQ9O_CE5';
const SEARCH = '(חשבונית OR קבלה OR invoice OR receipt) newer_than:90d';
const TIME_LIMIT_MS = 270000;

function saveInvoiceAttachments() {
  const start = Date.now();
  const folder = DriveApp.getFolderById(FOLDER_ID);
  const existing = new Set();
  const it = folder.getFiles();
  while (it.hasNext()) existing.add(it.next().getName());

  for (const thread of GmailApp.search(SEARCH, 0, 500)) {
    if (Date.now() - start > TIME_LIMIT_MS) {
      ScriptApp.newTrigger('saveInvoiceAttachments').timeBased().after(60000).create();
      console.log('time limit - auto-continuing in 1 minute');
      return;
    }
    for (const msg of thread.getMessages()) {
      const id = msg.getId();
      try {
        const atts = msg.getAttachments({ includeInlineImages: true, includeAttachments: true });
        let savedAny = false;
        for (const att of atts) {
          try {
            const type = att.getContentType() || '';
            const fname = att.getName() || '';
            if (!/pdf|jpe?g|png/i.test(type) && !/\.(pdf|jpe?g|png)$/i.test(fname)) continue;
            if (!att.getSize || att.getSize() === 0) continue;
            const safe = fname.replace(/[\/\\:*?"<>|]/g, '_').slice(0, 100) || 'file.pdf';
            const name = id + '_' + safe;
            savedAny = true;
            if (existing.has(name)) continue;
            const blob = att.copyBlob();
            blob.setName(name);
            folder.createFile(blob);
            existing.add(name);
          } catch (e) { console.log('skipped att: ' + id + ' - ' + e); }
        }
        // Fallback via Gmail advanced service for parts GmailApp cannot see.
        if (!savedAny && typeof Gmail !== 'undefined') {
          try {
            const m = Gmail.Users.Messages.get('me', id);
            const walk = (parts) => {
              if (!parts) return;
              for (const p of parts) {
                if (p.filename && /\.(pdf|jpe?g|png)$/i.test(p.filename) && p.body && p.body.attachmentId) {
                  const name = id + '_' + p.filename.replace(/[\/\\:*?"<>|]/g, '_').slice(0, 100);
                  if (!existing.has(name)) {
                    const att = Gmail.Users.Messages.Attachments.get('me', id, p.body.attachmentId);
                    folder.createFile(Utilities.newBlob(
                      Utilities.base64DecodeWebSafe(att.data), p.mimeType || 'application/pdf', name));
                    existing.add(name);
                    console.log('captured via API: ' + name);
                  }
                }
                walk(p.parts);
              }
            };
            walk(m.payload.parts);
          } catch (e) { console.log('api fetch failed: ' + id + ' - ' + e); }
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
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === 'saveInvoiceAttachments') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('saveInvoiceAttachments').timeBased().everyDays(1).atHour(6).create();
  console.log('done - everything synced; daily trigger re-armed');
}
