import React from 'react'
import klink from '../assets/klink.png'

const Navbar = () => {
  return (
    <div>
      <nav className='bg-slate-200 py-8 px-8 flex justify-between items-center'>
      <img
          src={klink}
          alt="Klink Pokémon"
          className="w-15 h-15"
        />
        <div className='font-bold text-2xl italic'>
            KlinkPPI
        </div>
      </nav>
    </div>
  )
}
export default Navbar
