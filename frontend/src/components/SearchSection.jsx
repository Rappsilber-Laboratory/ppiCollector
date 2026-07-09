import React, { useEffect, useState } from 'react'

const API_BASE_URL = 'http://127.0.0.1:8000'

const SearchSection = ({setresults}) => {
    const [from_database,setfrom_database]=useState('UniProtKB');
    const[protein_id,setprotein_id]=useState('');
    const [tax_id,settax_id]=useState('');
    const [species_name,setspecies_name]=useState('');
    const [speciesSuggestions,setspeciesSuggestions]=useState([])
    const [showSpeciesSuggestions,setshowSpeciesSuggestions]=useState(false)
    const [geneCandidates,setgeneCandidates]=useState([])
    const [selectedGeneCandidate,setselectedGeneCandidate]=useState(null)
    const [selected_databases,setselected_databases]=useState([])
    const [loading,setloading]=useState(false)
    const abortController = React.useRef(null)
    const speciesAbortController = React.useRef(null)
    const speciesSearchTimeout = React.useRef(null)

    useEffect(() => {
        const query = species_name.trim()

        if (!query) {
            setspeciesSuggestions([])
            return
        }

        speciesSearchTimeout.current = window.setTimeout(async () => {
            if (speciesAbortController.current) {
                speciesAbortController.current.abort()
            }

            speciesAbortController.current = new AbortController()

            try {
                const response = await fetch(
                    `${API_BASE_URL}/species/search?q=${encodeURIComponent(query)}&limit=20`,
                    { signal: speciesAbortController.current.signal }
                )

                if (!response.ok) {
                    setspeciesSuggestions([])
                    return
                }

                const data = await response.json()
                setspeciesSuggestions(data.results || [])
            } catch (error) {
                if (error.name !== 'AbortError') {
                    console.log(error)
                }
            }
        }, 150)

        return () => {
            if (speciesSearchTimeout.current) {
                clearTimeout(speciesSearchTimeout.current)
            }
        }
    }, [species_name])

    const clearGeneCandidateState = () => {
        setgeneCandidates([])
        setselectedGeneCandidate(null)
    }

    const performMainSearch = async (idValue, sourceDatabase) => {
        setloading(true)
        setresults(null)
        abortController.current = new AbortController()

        try{
            const params = new URLSearchParams({
                id_value: idValue,
                from_database: sourceDatabase
            })

            if (tax_id.trim()) {
                params.set('tax_id', tax_id.trim())
            }

            if (species_name.trim()) {
                params.set('species_name', species_name.trim())
            }

            if(selected_databases.length>0){
                selected_databases.forEach(value => params.append('selected_databases', value))
            }

            const response=await fetch(`${API_BASE_URL}/search?${params.toString()}`,{signal: abortController.current.signal});
            const data=await response.json();

            if(!response.ok){
                throw new Error(data.detail || 'Search failed')
            }

            setresults(data)
            settax_id(data?.[0]?.Input?.TaxonomyId || '')
            setspecies_name(data?.[0]?.Input?.SpeciesName || species_name)
            setshowSpeciesSuggestions(false)
            console.log(data);
        }catch(error){
          if(error.name==='AbortError'){
            console.log('Search Cancelled')
          } else {
            alert(error.message)
          }
          console.log(error)
        }finally{
          setloading(false)
        }
    }

    const handleGeneNameLookup = async () => {
        if (!species_name.trim() && !tax_id.trim()) {
            alert('Gene Name search requires a species name or taxonomy ID')
            return
        }

        setloading(true)
        abortController.current = new AbortController()

        try {
            const params = new URLSearchParams({
                query: protein_id
            })

            if (tax_id.trim()) {
                params.set('tax_id', tax_id.trim())
            }

            if (species_name.trim()) {
                params.set('species_name', species_name.trim())
            }

            const response = await fetch(
                `${API_BASE_URL}/gene-name/search?${params.toString()}`,
                { signal: abortController.current.signal }
            )
            const data = await response.json()

            if (!response.ok) {
                throw new Error(data.detail || 'Gene lookup failed')
            }

            const candidates = data.candidates || []
            setgeneCandidates(candidates)

            if (data.tax_id) {
                settax_id(data.tax_id)
            }

            if (data.species_name) {
                setspecies_name(data.species_name)
            }

            if (candidates.length === 0) {
                alert(`No UniProt matches found for gene name '${protein_id}'`)
                return
            }

            if (candidates.length === 1) {
                const [candidate] = candidates
                setselectedGeneCandidate(candidate)
                await performMainSearch(candidate.primary_accession, 'UniProtKB')
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('Search Cancelled')
            } else {
                alert(error.message)
            }
            console.log(error)
        } finally {
            setloading(false)
        }
    }

    const handleSearch=async ()=>{
        if(!protein_id || !from_database){
            alert('please complete the required input parameters')
            return
        }

        if (from_database === 'Gene_Name') {
            if (selectedGeneCandidate) {
                await performMainSearch(selectedGeneCandidate.primary_accession, 'UniProtKB')
                return
            }
            await handleGeneNameLookup()
            return
        }

        await performMainSearch(protein_id, from_database)
    }

    const handleCancel=()=>{
      if (abortController.current){
          abortController.current.abort()
          setloading(false)
      }
    }
    const handleDatabaseChange=(db)=>{
        const value=db.target.value;
        if(db.target.checked){
            setselected_databases([...selected_databases,value])
        }else{
            const index=selected_databases.indexOf(value);
            const size=(selected_databases).length;
            const arr1=selected_databases.slice(0,index);
            const arr2=selected_databases.slice(index+1,size)
            setselected_databases([...arr1,...arr2])
        }
    }

    const handleSpeciesSelect=(species)=>{
        clearGeneCandidateState()
        setspecies_name(species.display_name)
        settax_id(species.tax_id)
        setspeciesSuggestions([])
        setshowSpeciesSuggestions(false)
    }

    const handleGeneCandidateSelect = async (candidate) => {
        setselectedGeneCandidate(candidate)
        await performMainSearch(candidate.primary_accession, 'UniProtKB')
    }


  return (
    <div>
      <section className="bg-slate-200 py-20 px-4 sm:px-6">
      <div className="w-full max-w-[110rem] mx-auto">
        <div className="bg-white shadow-md rounded-2xl p-8 grid gap-8 lg:grid-cols-[minmax(18rem,24rem)_minmax(0,1fr)] lg:items-start">
        <div className="flex flex-col gap-4">
        <label className='font-bold text-left'>Databases Selections:</label>

        <div className="space-y-2">
        <label className="flex items-center gap-2">
        <input
            type="checkbox"
            value="String"
            onChange={handleDatabaseChange}
        />
        STRING
        </label>

        <label className="flex items-center gap-2">
        <input
            type="checkbox"
            value="IntAct"
            onChange={handleDatabaseChange}
        />
        IntAct
        </label>

        <label className="flex items-center gap-2">
        <input
            type="checkbox"
            value="BioGrid"
            onChange={handleDatabaseChange}
        />
        BioGRID
        </label>

        <label className="flex items-center gap-2">
        <input
            type="checkbox"
            value="Corum"
            onChange={handleDatabaseChange}
        />
        CORUM
        </label>

        <label className="flex items-center gap-2">
        <input
            type="checkbox"
            value="HuRI"
            onChange={handleDatabaseChange}
        />
        HuRI
        </label>

        <label className="flex items-center gap-2 mb-3">
        <input
            type="checkbox"
            value="Predictomes"
            onChange={handleDatabaseChange}
        />
        Predictomes
        </label>
        </div>
        </div>
        
        <div className="flex flex-col gap-4">
    <label className='font-bold text-left'>Input Type</label>
        <select
            value={from_database}
            onChange={(e) => {
                clearGeneCandidateState()
                setfrom_database(e.target.value)
            }}
            className="border border-gray-300  px-4 py-3 text-gray-700 focus:outline-none focus:ring-2 mb-3"
          >
            <option value="UniProtKB">UniProtKB</option>
            <option value="GeneID">GeneID</option>
            <option value="Ensembl">Ensembl</option>
            <option value="Gene_Name">Gene Name</option>
          </select>
        
          <label className='font-bold text-left'> Protein/Gene ID</label>
          <input
            type="text"
            placeholder="Enter Protein ID (e.g. Q9NYP3)"
            value={protein_id}
            onChange={(e) => {
                clearGeneCandidateState()
                setprotein_id(e.target.value.toUpperCase())
            }}
            className="border border-gray-300  px-4 py-3 text-gray-700 focus:outline-none focus:ring-2 mb-3"
          />

        <label className='font-bold text-left'> Species Name (optional)</label>
          <div className="relative">
            <input
              type="text"
              placeholder="Type a species (e.g. human, mus musculus)"
              value={species_name}
              onChange={(e) => {
                clearGeneCandidateState()
                setspecies_name(e.target.value)
                setshowSpeciesSuggestions(true)
              }}
              onFocus={() => {
                if (speciesSuggestions.length > 0) {
                  setshowSpeciesSuggestions(true)
                }
              }}
              onBlur={() => {
                window.setTimeout(() => setshowSpeciesSuggestions(false), 150)
              }}
              className="border border-gray-300 px-4 py-3 text-gray-700 focus:outline-none focus:ring-2 w-full"
            />

            {showSpeciesSuggestions && speciesSuggestions.length > 0 && (
              <div className="absolute z-20 mt-2 max-h-72 w-full overflow-y-auto rounded-xl border border-gray-200 bg-white shadow-lg">
                {speciesSuggestions.map(species => (
                  <button
                    key={species.tax_id}
                    type="button"
                    onMouseDown={(event) => {
                      event.preventDefault()
                      handleSpeciesSelect(species)
                    }}
                    className="flex w-full flex-col gap-1 border-b border-gray-100 px-4 py-3 text-left last:border-b-0 hover:bg-slate-50"
                  >
                    <span className="font-medium text-slate-800">{species.display_name}</span>
                    <span className="text-xs text-slate-500">
                      Taxonomy ID: {species.tax_id} • Databases: {species.supported_databases.join(', ')}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <p className="text-sm text-gray-500">
            You can search with a taxonomy ID, a species name, both, or neither. Adding one improves organism matching.
          </p>

          {from_database === 'Gene_Name' && (
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <p className="font-semibold text-slate-800">Gene Name Search</p>
              <p className="mt-1 text-sm text-slate-600">
                Gene symbols are matched against UniProt candidates for the selected species before the interaction search runs.
              </p>
              {selectedGeneCandidate && (
                <p className="mt-3 text-sm text-slate-700">
                  Selected match: <strong>{selectedGeneCandidate.primary_accession}</strong>
                  {' '}({selectedGeneCandidate.gene_names.join(', ') || 'No gene symbol'})
                </p>
              )}
            </div>
          )}

        <label className='font-bold text-left'> Taxonomy ID (optional)</label>
          <input
            type="number"
            placeholder="Enter Taxonomy ID (e.g. 9606 for Human)"
            value={tax_id}
            onChange={(e) => {
                clearGeneCandidateState()
                settax_id(e.target.value)
            }}
            className="border border-gray-300  px-4 py-3 text-gray-700 focus:outline-none focus:ring-2"
          />

          <div className="flex flex-col gap-3 pt-2 sm:flex-row">
            <button
              onClick={handleSearch}
              className="bg-blue-900 text-white py-3 px-6 font-semibold hover:bg-blue-600 transition sm:min-w-40"
            >
              {from_database === 'Gene_Name' && !selectedGeneCandidate ? 'Find Matches' : 'Search'}
            </button>

            <button
              onClick={handleCancel}
              className="bg-gray-800 text-white py-3 px-6 font-semibold hover:bg-gray-600 transition sm:min-w-40"
            >
              Cancel
            </button>
          </div>
          {loading && (
          <div className="text-center lg:text-left">
            <p className="text-blue-900 font-semibold mb-3">Searching databases...</p>
            <div className="flex flex-col gap-2">
              {(selected_databases.length > 0 ? selected_databases:['String', 'IntAct', 'BioGrid', 'Corum', 'Predictomes', 'HuRI']).map(db => (
                <div key={db} className="flex items-center gap-2 text-gray-600 justify-center lg:justify-start">
                    <div className="animate-pulse w-2 h-2  bg-blue-900"></div>
                    Searching {db}...
                </div>
              ))}
          </div>
        </div>
          )}
        </div>
        {from_database === 'Gene_Name' && geneCandidates.length > 0 && (
          <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-6 lg:col-span-2">
            <h3 className="text-lg font-semibold text-slate-900">Matched UniProt Entries</h3>
            <p className="mt-1 text-sm text-slate-600">
              Select the intended entry to continue the interaction search.
            </p>
            <div className="mt-4 flex flex-col gap-3">
              {geneCandidates.map(candidate => (
                <button
                  key={candidate.primary_accession}
                  type="button"
                  onClick={() => handleGeneCandidateSelect(candidate)}
                  className={`rounded-xl border px-4 py-4 text-left shadow-sm transition ${
                    selectedGeneCandidate?.primary_accession === candidate.primary_accession
                      ? 'border-blue-700 bg-blue-50 ring-2 ring-blue-200'
                      : 'border-slate-200 bg-white hover:border-slate-400 hover:bg-slate-100'
                  }`}
                >
                  <div className="flex flex-col gap-1">
                    <span className="font-semibold text-slate-900">
                      {candidate.primary_accession} {candidate.reviewed ? '• Reviewed' : '• Unreviewed'}
                    </span>
                    <span className="text-sm text-slate-700">
                      {candidate.gene_names.length > 0 ? candidate.gene_names.join(', ') : 'No gene names returned'}
                    </span>
                    <span className="text-sm text-slate-600">
                      {candidate.protein_name || 'No protein name returned'}
                    </span>
                    <span className="text-xs text-slate-500">
                      {candidate.organism_name} • Taxonomy ID: {candidate.tax_id}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
      </div>
    </section>
    </div>
  )
}

export default SearchSection
