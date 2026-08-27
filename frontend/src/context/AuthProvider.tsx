import { createContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import type { User, Session, SignInWithPasswordCredentials, SignUpWithPasswordCredentials } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'

export interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signUp: (credentials: SignUpWithPasswordCredentials & { options?: { data?: { name?: string } } }) => Promise<any>
  signIn: (credentials: SignInWithPasswordCredentials) => Promise<void>
  signOut: () => Promise<void>
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    // 1. Fetch current session on mount to restore existing sessions
    const getInitialSession = async () => {
      try {
        const { data: { session: initialSession }, error } = await supabase.auth.getSession()
        if (error) {
          console.error('Error fetching initial session:', error.message)
        }
        if (initialSession) {
          setSession(initialSession)
          setUser(initialSession.user)
        }
      } catch (err) {
        console.error('Unexpected error fetching initial session:', err)
      } finally {
        setLoading(false)
      }
    }

    getInitialSession()

    // 2. Listen to authentication state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, currentSession) => {
      setSession(currentSession)
      setUser(currentSession?.user ?? null)
      setLoading(false)
    })

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  const signUp = async (credentials: SignUpWithPasswordCredentials & { options?: { data?: { name?: string } } }) => {
    setLoading(true)
    try {
      const { data, error } = await supabase.auth.signUp(credentials)
      if (error) throw error
      return data
    } finally {
      setLoading(false)
    }
  }

  const signIn = async (credentials: SignInWithPasswordCredentials) => {
    setLoading(true)
    try {
      const { error } = await supabase.auth.signInWithPassword(credentials)
      if (error) throw error
    } finally {
      setLoading(false)
    }
  }

  const signOut = async () => {
    setLoading(true)
    try {
      const { error } = await supabase.auth.signOut()
      if (error) throw error
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthContext.Provider value={{ user, session, loading, signUp, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}
