const ISFT_PROTOCOL = 'isft-sheets-v1';
const ISFT_TAB = 'Arizalar';
const ISFT_HEADERS = [
  'Ariza №', 'Yuborilgan vaqt', 'Ism', 'Familiya', 'Otasining ismi',
  'Telefon', 'Tug‘ilgan sana', 'Yo‘nalish', 'Ta’lim shakli', 'Rozilik',
  'Holat', 'Sinxron ID', 'Versiya',
];
const ISFT_FIELDS = [
  'id', 'created_at', 'first_name', 'last_name', 'father_name', 'phone',
  'birth_date', 'program', 'study_type', 'consent', 'status',
];

function doPost(event) {
  let data;
  try {
    data = JSON.parse(event.postData.contents);
  } catch (_) {
    return reply_({ok: false, code: 'payload'});
  }
  const properties = PropertiesService.getScriptProperties();
  const secret = properties.getProperty('ISFT_SYNC_SECRET');
  const spreadsheetId = properties.getProperty('ISFT_SHEET_ID');
  if (!data || data.protocol !== ISFT_PROTOCOL || !secret ||
      !/^[A-Za-z0-9_-]{32,128}$/.test(secret) || !matches_(data.secret, secret)) {
    return reply_({ok: false, code: 'auth'});
  }
  if (!spreadsheetId || (data.spreadsheet_id && data.spreadsheet_id !== spreadsheetId)) {
    return reply_({ok: false, code: 'target'});
  }
  if (!Array.isArray(data.rows) || data.rows.length > 25 || !data.rows.every(validRow_)) {
    return reply_({ok: false, code: 'payload'});
  }

  const lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) return reply_({ok: false, code: 'busy'});
  try {
    const book = SpreadsheetApp.openById(spreadsheetId);
    const sheet = book.getSheetByName(ISFT_TAB) || book.insertSheet(ISFT_TAB);
    if (sheet.getLastRow() === 0) {
      sheet.getRange(1, 1, 1, ISFT_HEADERS.length).setValues([ISFT_HEADERS])
        .setFontWeight('bold').setBackground('#eeeeee');
      sheet.setFrozenRows(1);
      sheet.hideColumns(ISFT_HEADERS.length - 1, 2);
    }
    const headers = sheet.getRange(1, 1, 1, ISFT_HEADERS.length).getValues()[0];
    if (ISFT_HEADERS.some((label, index) => headers[index] !== label)) {
      return reply_({ok: false, code: 'header'});
    }
    if (data.rows.length) upsertRows_(sheet, data.rows);
    SpreadsheetApp.flush();
    return reply_({
      ok: true, spreadsheet_id: spreadsheetId, keys: data.rows.map(row => row.submission_key),
    });
  } catch (_) {
    return reply_({ok: false, code: 'write'});
  } finally {
    lock.releaseLock();
  }
}

function upsertRows_(sheet, rows) {
  let last = sheet.getLastRow();
  const known = new Map();
  if (last > 1) {
    const keys = sheet.getRange(2, ISFT_HEADERS.length - 1, last - 1, 2).getValues();
    keys.forEach(([key, version], index) => {
      if (key) known.set(key, {row: index + 2, version: Number(version)});
    });
  }
  for (const item of rows) {
    const key = 'isft:' + item.submission_key;
    const previous = known.get(key);
    if (previous && previous.version >= item.sync_version) continue;
    const rowNumber = previous ? previous.row : ++last;
    if (rowNumber > sheet.getMaxRows()) sheet.insertRowsAfter(sheet.getMaxRows(), 100);
    const values = ISFT_FIELDS.map(field => {
      if (field === 'consent') return item.consent === 1 ? 'Ha' : 'Ko‘rsatilmagan';
      return item[field] == null ? '' : String(item[field]);
    });
    // Keep submitted values literal, including +998 numbers, dates and text starting with "=".
    const cells = values.map(value => value ? "'" + value : '');
    cells.push(key, item.sync_version);
    sheet.getRange(rowNumber, 1, 1, cells.length).setValues([cells]);
    known.set(key, {row: rowNumber, version: item.sync_version});
  }
}

function validRow_(row) {
  return row && typeof row.submission_key === 'string' && /^[0-9a-f]{32}$/.test(row.submission_key) &&
    Number.isSafeInteger(row.id) && row.id > 0 &&
    Number.isSafeInteger(row.sync_version) && row.sync_version > 0 &&
    ISFT_FIELDS.every(field => {
      if (field === 'id') return true;
      if (field === 'consent') return row[field] === 1 || row[field] === null;
      return row[field] === null || (typeof row[field] === 'string' && row[field].length <= 1000);
    });
}

function matches_(provided, expected) {
  if (typeof provided !== 'string' || provided.length !== expected.length) return false;
  let difference = 0;
  for (let index = 0; index < expected.length; index++) {
    difference |= provided.charCodeAt(index) ^ expected.charCodeAt(index);
  }
  return difference === 0;
}

function reply_(result) {
  return ContentService.createTextOutput(JSON.stringify({protocol: ISFT_PROTOCOL, ...result}))
    .setMimeType(ContentService.MimeType.JSON);
}
