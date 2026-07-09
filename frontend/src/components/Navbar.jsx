import React from 'react'
import klink from '../assets/klink.png'

const Navbar = () => {
  return (
    <nav className="bg-slate-200 px-6 py-6">
      <div className="mx-auto grid w-full max-w-[90rem] grid-cols-[auto_1fr_auto] items-center gap-4">
        <img
          src={klink}
          alt="Klink Pokemon"
          className="h-20 w-20 object-contain sm:h-24 sm:w-24"
        />
        <div className="px-2 text-center">
          <h1 className="text-xl font-bold italic leading-tight text-slate-900 sm:text-2xl lg:text-3xl">
            KlinkPPI: Standards-Compliant Protein-Protein Interaction Search Across Major Interaction Databases
          </h1>
        </div>
        <div className="h-20 w-20 sm:h-24 sm:w-24" aria-hidden="true" />
      </div>
    </nav>
  )
}
export default Navbar
