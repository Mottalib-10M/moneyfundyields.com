interface Props { id: string; label: string; options: Array<{ value: string; label: string }>; value: string; onChange: (v: string) => void; className?: string }
export default function Toggle({ id, label, options, value, onChange, className = '' }: Props) {
  return (
    <div className={`grid grid-rows-subgrid row-span-3 content-start gap-y-0 ${className}`} role="group" aria-labelledby={`${id}-label`}>
      <span id={`${id}-label`} className="mb-1 block text-sm font-medium text-navy-700">{label}</span>
      <div className="grid h-12 w-fit min-w-[9rem] grid-flow-col auto-cols-fr gap-1 self-start rounded-lg border border-navy-300 bg-white p-1">
        {options.map((o) => (
          <button key={o.value} type="button" onClick={() => onChange(o.value)} aria-pressed={value === o.value}
            className={`h-full whitespace-nowrap rounded-md px-4 text-sm font-medium transition-colors ${value === o.value ? 'bg-accent-600 text-white' : 'text-navy-600 hover:bg-navy-50'}`}>{o.label}</button>
        ))}
      </div>
    </div>
  );
}
