# PHR: ChatKit Import Fix - ReferenceError Resolution

**Date**: 2026-01-07
**Author**: Claude Code (Sonnet 4.5)
**Branch**: main
**Stage**: agent

---

## Issue

User reported: `"ChatKit is not defined" ReferenceError in ChatInterface.tsx`

The error occurred because:
1. ChatKit is a **web component** (`<openai-chatkit>`), not a standard React component
2. The `@openai/chatkit` package only contains TypeScript type definitions
3. The actual web component is bundled inside `@openai/chatkit-react`
4. The React wrapper (`ChatKit` component) must be imported and used correctly

---

## Root Cause Analysis

**Package Structure Discovery**:
```
@openai/chatkit (1.2.0)
├── Only contains type definitions (.d.ts)
└── No JavaScript implementation

@openai/chatkit-react (1.4.0)  ← THIS is the main package
├── Contains React wrapper component
├── Contains useChatKit hook
└── Bundles the <openai-chatkit> web component
```

**Incorrect Import Pattern** (original):
```typescript
import { useChatKit } from '@openai/chatkit-react';
// ...
<ChatKit />  // ERROR: ChatKit not exported as React component
```

**Correct Import Pattern**:
```typescript
import { ChatKit, useChatKit, ChatKitControl } from '@openai/chatkit-react';
// ...
<ChatKit control={control} ref={ref} className="h-full w-full" />
```

---

## Solution Applied

**File**: `frontend/src/components/chat/ChatInterface.tsx`

**Changes**:
1. Added `ChatKit` to imports:
   ```typescript
   import { ChatKit, useChatKit, ChatKitControl } from '@openai/chatkit-react';
   ```

2. Removed incorrect web component import:
   ```typescript
   // REMOVED: import '@openai/chatkit';  (Not needed - bundled in react package)
   ```

3. Used React wrapper component correctly:
   ```tsx
   <ChatKit
     control={control}
     ref={ref}
     className="h-full w-full"
   />
   ```

4. Updated CSS selectors to target web component via React wrapper:
   ```css
   .chatkit-container openai-chatkit::part(message-user) { ... }
   ```

---

## Technical Details

The `@openai/chatkit-react` package exports:
- `ChatKit` - React component (forwardRef) that wraps `<openai-chatkit>`
- `useChatKit(options)` - Hook that returns `{ control, ref, methods }`
- `ChatKitControl` - Type for the control object
- `UseChatKitOptions` - Type for hook options
- `UseChatKitReturn` - Type for hook return value

The React component automatically:
- Registers the `openai-chatkit` custom element
- Sets options via `el.setOptions(control.options)`
- Attaches event handlers for all ChatKit events
- Manages instance lifecycle via `control.setInstance()`

---

## Files Modified

1. `frontend/src/components/chat/ChatInterface.tsx` - Fixed imports and component usage

---

## Verification

After fix, the component should:
1. Compile without TypeScript errors
2. Render the `<openai-chatkit>` web component
3. Connect to `/api/chatkit` endpoint
4. Show "Ready" state after initialization

---

## Lessons Learned

1. ChatKit is a web component first, React wrapper second
2. Always check `package.json` to understand what's actually bundled
3. Type definition packages (`@openai/chatkit`) don't contain runtime code
4. The main package for React usage is `@openai/chatkit-react`
5. The web component auto-registers when the React component mounts
