// Auto-sync Gmail invoice attachments to the Drive folder "חשבוניות למעקב 📥".
// One-time setup (2 minutes):
//   1. Open https://script.google.com → New project
//   2. Paste this whole file, save
//   3. Run saveInvoiceAttachments once → approve the consent screen
//   4. Run setupDailyTrigger once → done, hands-free forever
//
// Files are named "<gmailMessageId>_<originalName>" so the invoice-collector
// skill can match each file back to its ledger row by gmail_message_id.

const FOLDER_ID = '1-EdHr7QezErSBkOiX83d5Yx7JQ9O_CE5';
const SEARCH = '(חשבונית OR קבלה OR invoice OR receipt) has:attachment newer_than:60d';

function saveInvoiceAttachments() {
  const folder = DriveApp.getFolderById(FOLDER_ID);
  const existing = new Set();
  const it = folder.getFiles();
  while (it.hasNext()) existing.add(it.next().getName());

  for (const thread of GmailApp.search(SEARCH, 0, 400)) {
    for (const msg of thread.getMessages()) {
      for (const att of msg.getAttachments({ includeInlineImages: false })) {
        if (!/pdf|jpe?g|png/i.test(att.getContentType())) continue;
        const name = msg.getId() + '_' + att.getName();
        if (existing.has(name)) continue;
        folder.createFile(att.copyBlob().setName(name));
        existing.add(name);
      }
    }
  }
}

function setupDailyTrigger() {
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('saveInvoiceAttachments').timeBased().everyDays(1).atHour(6).create();
}
