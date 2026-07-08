import React from 'react'
import { useState } from 'react'

const SearchSection = ({setresults}) => {
    const [from_database,setfrom_database]=useState('UniProtKB');
    const[protein_id,setprotein_id]=useState('');
    const [tax_id,settax_id]=useState('');
    const [selected_databases,setselected_databases]=useState([])
    const [loading,setloading]=useState(false)
    // const [results,setresults]=useState(null)
    const abortController = React.useRef(null)

    const handleSearch=async ()=>{
        if(!protein_id || !tax_id || !from_database){
            alert('please complete all the input parameters')
            return
        }
        setloading(true)
        setresults(null)
        abortController.current = new AbortController()
        try{
            let url=`http://127.0.0.1:8000/search?id_value=${protein_id}&from_database=${from_database}&tax_id=${tax_id}`;
            if(selected_databases.length>0){
                selected_databases.forEach((value,index,array)=>url+=`&selected_databases=${value}`)
            }
            const response=await fetch(url,{signal: abortController.current.signal});
            const data=await response.json();
            setresults(data)
            console.log(data);
        }catch(error){
          if(error.name==='AbortError'){
            console.log('Search Cancelled')
          }
          console.log(error)
        }finally{
          setloading(false)
        }
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


  return (
    <div>
      <section className="bg-slate-200 py-20 px-6">
      <div className="max-w-3xl mx-auto text-center">
        <h1 className="text-4xl font-bold mb-4 italic font-sans">
          Search for a Protein
        </h1>
        <p className="text-gray-500 mb-10 text-lg italic">
        Get Detailed Data of Interactions with your Queried Protein
        </p>

        <div className="bg-white shadow-md p-8 flex flex-col gap-4">
        
        <label className='font-bold text-left'>Select Your Databases:</label>

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
        
    <label className='font-bold text-left'>Select Your Input Type</label>
        <select
            value={from_database}
            onChange={(e) => setfrom_database(e.target.value)}
            className="border border-gray-300  px-4 py-3 text-gray-700 focus:outline-none focus:ring-2 mb-3"
          >
            <option value="UniProtKB">UniProtKB</option>
            <option value="GeneID">GeneID</option>
            <option value="Ensembl">Ensembl</option>
            <option value="Gene_Name">Gene Name</option>
          </select>
        
          <label className='font-bold text-left'>Enter the Protein/Gene ID</label>
          <input
            type="text"
            placeholder="Enter Protein ID (e.g. Q9NYP3)"
            value={protein_id}
            onChange={(e) =>setprotein_id(e.target.value.toUpperCase())}
            className="border border-gray-300  px-4 py-3 text-gray-700 focus:outline-none focus:ring-2 mb-3"
          />

        <label className='font-bold text-left'>Enter the Taxonomy ID</label>
          <input
            type="number"
            placeholder="Enter Taxonomy ID (e.g. 9606 for Human)"
            value={tax_id}
            onChange={(e) => settax_id(e.target.value)}
            className="border border-gray-300  px-4 py-3 text-gray-700 focus:outline-none focus:ring-2"
          />

          <button
            onClick={handleSearch}
            className="bg-blue-900 text-white py-3  font-semibold hover:bg-blue-600 transition w-1/3"
          >
            Search
          </button>

          <button
            onClick={handleCancel}
            className="bg-gray-800 text-white py-3  font-semibold hover:bg-gray-600 transition w-1/3 "
          >
            Cancel
          </button>
          {loading && (
          <div className=" text-center">
            <p className="text-blue-900 font-semibold mb-3">Searching databases...</p>
            <div className="flex flex-col gap-2">
              {(selected_databases.length > 0 ? selected_databases:['String', 'IntAct', 'BioGrid', 'Corum', 'Predictomes', 'HuRI']).map(db => (
                <div key={db} className="flex items-center gap-2 text-gray-600 justify-center">
                    <div className="animate-pulse w-2 h-2  bg-blue-900"></div>
                    Searching {db}...
                </div>
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
