import './NavBar.css'
import {Link} from 'react-router-dom'


const NavBar = () => {

    return (
        <nav className="nav">
        <ul>
        <li> <Link to = "/">home</Link></li>
        <li><Link to="/about">about us</Link></li>
        <li><Link to="/resources">resources</Link></li>
        </ul>
        </nav>
        
    );
}

export default NavBar;