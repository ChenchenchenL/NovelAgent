import { useState } from 'react'

export function useUndoRedo() {
  const [undoStack, setUndoStack] = useState([])
  const [redoStack, setRedoStack] = useState([])

  const pushState = (currentVal) => {
    setUndoStack((prev) => [...prev.slice(-49), currentVal])
    setRedoStack([])
  }

  const undo = (currentVal, setter) => {
    if (undoStack.length === 0) return
    const prevVal = undoStack[undoStack.length - 1]
    setRedoStack((prev) => [...prev, currentVal])
    setUndoStack((prev) => prev.slice(0, -1))
    setter(prevVal)
  }

  const redo = (currentVal, setter) => {
    if (redoStack.length === 0) return
    const nextVal = redoStack[redoStack.length - 1]
    setUndoStack((prev) => [...prev, currentVal])
    setRedoStack((prev) => prev.slice(0, -1))
    setter(nextVal)
  }

  const resetStacks = () => {
    setUndoStack([])
    setRedoStack([])
  }

  return {
    canUndo: undoStack.length > 0,
    canRedo: redoStack.length > 0,
    pushState,
    undo,
    redo,
    resetStacks,
  }
}
