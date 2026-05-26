/**
 * ModelToggle — OSS / Frontier pill selector.
 * Fits inside the header bar, sharp edges, accent highlight on active.
 */
export default function ModelToggle({ model, onChange }) {
  const options = [
    { value: 'frontier', label: 'GPT-4.1',      sub: 'frontier' },
    { value: 'oss',      label: 'Qwen 2.5-0.5B', sub: 'oss'      },
  ]

  return (
    <div className="flex items-stretch h-8 border border-border font-mono text-xs">
      {options.map(({ value, label, sub }, i) => {
        const active = model === value
        return (
          <button
            key={value}
            onClick={() => onChange(value)}
            className={[
              'flex flex-col items-center justify-center px-4 transition-colors duration-150 cursor-pointer select-none',
              i === 0 ? 'border-r border-border' : '',
              active
                ? 'bg-accent text-bg font-medium'
                : 'bg-surface text-dim hover:text-text hover:bg-muted/30',
            ].join(' ')}
          >
            <span className="leading-none tracking-tight">{label}</span>
            <span className={['text-[9px] mt-0.5 leading-none uppercase tracking-widest', active ? 'text-bg/60' : 'text-muted'].join(' ')}>
              {sub}
            </span>
          </button>
        )
      })}
    </div>
  )
}