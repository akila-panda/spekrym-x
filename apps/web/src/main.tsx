import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import { DataProvider } from './data/DataProvider'
import './index.css'
const client = new QueryClient()
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><QueryClientProvider client={client}><DataProvider><App /></DataProvider></QueryClientProvider></React.StrictMode>)
