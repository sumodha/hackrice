import './App.css';
import HomePage from './HomePage.jsx'
import AboutPage from './AboutPage.jsx'
import ResourcesPage from './ResourcesPage.jsx'
import NavBar from './NavBar.jsx'

import {  BrowserRouter as Router, Routes, Route } from 'react-router-dom';


const App = () => {
  return (
    <>
    <NavBar></NavBar>
      <>
      <Routes>
        <Route path ="/" element = {<HomePage></HomePage>}></Route>
        <Route path ="/about" element = {<AboutPage></AboutPage>}></Route>
        <Route path ="/resources" element = {<ResourcesPage></ResourcesPage>}></Route>
      </Routes>
      </>

    </>

  );
}

export default App;
