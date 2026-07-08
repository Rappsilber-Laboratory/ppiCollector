const DBHeader = ({ name, subtitle, count, color }) => (
    <div className={`${color} px-6 py-4 flex justify-between items-center`}>
        <div>
            <h2 className="text-white text-lg font-semibold tracking-wide">{name}</h2>
            <p className="text-white/50 text-xs mt-0.5">{subtitle}</p>
        </div>
        <span className="bg-white/10 text-white/80 text-xs font-medium px-3 py-1  border-white/20">
            {count} interactors
        </span>
    </div>
)

export default DBHeader