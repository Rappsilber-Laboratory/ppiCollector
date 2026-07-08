import { useState } from 'react'

const INITIAL_SHOW = 20

const InfoButton = ({ info }) => {
    const [visible, setVisible] = useState(false);

    return (
        <span className="relative inline-flex items-center">
            <button
                onMouseEnter={() => setVisible(true)}
                onMouseLeave={() => setVisible(false)}
                className="w-5 h-5 rounded-full bg-blue-100 text-blue-600 border border-blue-300 text-xs font-bold flex items-center justify-center"
            >
                i
            </button>

            {visible && (
                <div
                className="
                absolute
                top-8
                left-1/2
                -translate-x-1/2
                z-50
                max-w-sm
                p-4
                rounded-lg
                bg-white
                border
                border-gray-200
                shadow-xl
                text-xs
                font-normal
                normal-case
                text-gray-600
                whitespace-normal
                break-words
                leading-relaxed
                "
            >
                {info}
            </div>
            )}
        </span>
    );
};

const DBTable = ({ headers, rows }) => {
    const [expanded, setexpanded] = useState(false)

    const visibleRows = expanded ? rows : rows.slice(0, INITIAL_SHOW)
    const hasMore = rows.length > INITIAL_SHOW

    return (
        <div>
            <div className="overflow-x-auto  border-gray-200">
                <table className="w-full text-sm text-left">
                    <thead className="bg-gray-50 text-gray-500 text-xs uppercase tracking-wide">
                        <tr>
                            <th className="px-4 py-3">Rank</th>
                            {headers.map(h => (
                                <th key={h.label} className="px-4 py-3 whitespace-nowrap">
                                    {h.label}
                                    {h.info && <InfoButton info={h.info} />}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {visibleRows.map((row, index) => (
                            <tr key={index} className="hover:bg-gray-50 transition">
                                <td className="px-4 py-3 text-gray-400 font-medium">{index + 1}</td>
                                {row}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {hasMore && (
                <button
                    onClick={() => setexpanded(!expanded)}
                    className="mt-3 w-full text-sm text-gray-500 hover:text-gray-700 border border-gray-200  py-2 hover:bg-gray-50 transition"
                >
                    {expanded
                        ? `▲ Show less`
                        : `▼ Show ${rows.length - INITIAL_SHOW} more interactions`}
                </button>
            )}
        </div>
    )
}

export default DBTable