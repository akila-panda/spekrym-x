import { useQuery } from '@tanstack/react-query'
import { fetchExp001 } from '../labApi'

export const useExp001 = () =>
  useQuery({ queryKey: ['lab-exp001'], queryFn: ({ signal }) => fetchExp001(signal), retry: false, staleTime: 60_000 })
