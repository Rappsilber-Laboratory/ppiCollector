const MetadataCard = ({ fields }) => (
    <div className="px-6 py-4 bg-gray-50 border-b border-gray-100 flex flex-wrap gap-6">
        {fields.map(({ label, value }) => (
            value && (
                <div key={label}>
                    <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">{label}</p>
                    {Array.isArray(value) ? (
                        <ul className="list-disc list-inside text-gray-600 text-sm space-y-0.5">
                            {value.map((v, i) => <li key={i}>{v}</li>)}
                        </ul>
                    ) : (
                        <p className="text-gray-700 text-sm font-medium">{value}</p>
                    )}
                </div>
            )
        ))}
    </div>
)

export default MetadataCard