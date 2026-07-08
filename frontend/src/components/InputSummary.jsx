import React from 'react'

const InputSummary = ({input}) => {
  return (
    <div className='bg-blue-100 p-6 mb-8'>
      <h2 className='font-bold text-2xl mb-4'>Search Summary</h2>
      <p>
        <strong>Protein:</strong>{input.UniProtId}
      </p>
      <p>
        <strong>Taxonomy Id:</strong>{input.TaxonomyId}
      </p>
    </div>
  );
}
export default InputSummary
