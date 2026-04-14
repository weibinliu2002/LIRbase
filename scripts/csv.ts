export interface CsvColumn<T> {
  key: keyof T | string
  label: string
  formatter?: (row: T) => unknown
}

function escapeCsvCell(value: unknown): string {
  if (value === null || value === undefined) return ''
  const raw = String(value)
  const escaped = raw.replace(/"/g, '""')
  if (/[",\n]/.test(escaped)) {
    return `"${escaped}"`
  }
  return escaped
}

export function downloadRowsAsCsv<T extends object>(
  rows: T[],
  columns: CsvColumn<T>[],
  filename: string
) {
  const header = columns.map(col => escapeCsvCell(col.label)).join(',')
  const body = rows.map((row) => {
    return columns
      .map((col) => {
        const record = row as Record<string, unknown>
        const value = col.formatter ? col.formatter(row) : record[String(col.key)]
        return escapeCsvCell(value)
      })
      .join(',')
  })
  const csvContent = [header, ...body].join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
