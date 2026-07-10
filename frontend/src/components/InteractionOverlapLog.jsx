const getDbEntries = (dbName, dbValue) => {
  if (!dbValue || typeof dbValue === 'string') {
    return []
  }

  if (dbName === 'String') {
    return dbValue?.[1]?.Direct_Interactions || []
  }

  if (dbName === 'IntAct') {
    return dbValue?.[1]?.Interactions || []
  }

  return dbValue?.[1]?.Interactors || []
}

const normalizeKey = (value) => String(value || '').trim().toUpperCase()

const buildOverlapEntries = (results) => {
  const output = results?.[1]?.output || []
  const searchedDatabases = output.map(item => Object.keys(item)[0]).filter(Boolean)
  const overlapMap = new Map()

  for (const item of output) {
    const dbName = Object.keys(item)[0]
    const dbValue = item[dbName]
    const entries = getDbEntries(dbName, dbValue)

    for (const entry of entries) {
      const geneName = entry.Interactor_Gene_Name || entry.Interactor_A || null
      const interactorId = entry.Interactor_A || null
      const key = normalizeKey(geneName || interactorId)
      if (!key) {
        continue
      }

      if (!overlapMap.has(key)) {
        overlapMap.set(key, {
          geneNames: new Set(),
          ids: new Set(),
          databases: new Set(),
        })
      }

      const aggregate = overlapMap.get(key)
      if (geneName) {
        aggregate.geneNames.add(geneName)
      }
      if (interactorId) {
        aggregate.ids.add(interactorId)
      }
      aggregate.databases.add(dbName)
    }
  }

  const overlapEntries = Array.from(overlapMap.values())
    .filter(item => item.databases.size >= 1)
    .map(item => ({
      geneName: Array.from(item.geneNames)[0] || Array.from(item.ids)[0] || '-',
      interactorId: Array.from(item.ids)[0] || '-',
      databases: Array.from(item.databases).sort(),
      count: item.databases.size,
    }))
    .sort((a, b) => b.count - a.count || a.geneName.localeCompare(b.geneName))

  return { searchedDatabases, overlapEntries }
}

const InteractionOverlapLog = ({ results }) => {
  const input = results?.[0]?.Input || {}
  const { searchedDatabases, overlapEntries } = buildOverlapEntries(results)
  const queryLabel = input.OriginalInput || input.UniProtId || '-'
  const queryType = input.OriginalInputType || 'UniProtKB'

  return (
    <div className="mb-8 rounded-2xl border border-slate-200 bg-slate-50 p-6 shadow-sm">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Shared Interaction Log</h2>
          <p className="text-sm text-slate-600">
            Query: <span className="font-semibold text-slate-800">{queryLabel}</span>
            {' '}<span className="text-slate-500">({queryType})</span>
          </p>
        </div>
        <p className="text-sm text-slate-600">
          Databases searched: <span className="font-semibold text-slate-800">{searchedDatabases.join(', ') || '-'}</span>
        </p>
      </div>

      {overlapEntries.length > 0 ? (
        <div className="mt-5 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-3 py-3">Interactor</th>
                <th className="px-3 py-3">ID</th>
                <th className="px-3 py-3">Found In</th>
                <th className="px-3 py-3">Databases</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {overlapEntries.map((entry) => (
                <tr key={`${entry.geneName}-${entry.interactorId}`} className="align-top">
                  <td className="px-3 py-3 font-semibold text-slate-900">{entry.geneName}</td>
                  <td className="px-3 py-3 text-slate-600">{entry.interactorId}</td>
                  <td className="px-3 py-3 text-slate-700">{entry.count} databases</td>
                  <td className="px-3 py-3 text-slate-600">{entry.databases.join(', ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="mt-5 rounded-xl border border-dashed border-slate-300 bg-white px-4 py-5 text-sm text-slate-500">
          No interactors were found in the searched databases for this query.
        </div>
      )}
    </div>
  )
}

export default InteractionOverlapLog
