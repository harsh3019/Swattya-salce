# Lead Change Status Modal

A React component for changing lead status with opportunity conversion support.

## Features

- **Lead Preview Card**: Shows lead name, company, contact number, email, and current status
- **Dynamic Status Dropdown**: Initial options are "Approved" and "Rejected"
- **Conditional Conversion**: "Convert to Opportunity" option appears only after successful approval
- **Accessibility**: Full keyboard navigation, focus trapping, ESC to close
- **Toast Notifications**: Non-blocking success messages
- **API Integration**: Handles status changes and opportunity creation

## API Endpoints

### 1. Change Lead Status
```
POST /api/leads/{leadId}/status
Content-Type: application/json

Request:
{
  "status": "approved" | "Rejected" | "convert_to_opp"
}

Response (Approval):
{
  "success": true,
  "lead": { ...updated lead data... },
  "converted": false
}

Response (Conversion):
{
  "success": true,
  "lead": { ...updated lead data... },
  "converted": true,
  "opportunity_id": "POT-A1B2C3D4"
}
```

### 2. Opportunity Creation
The server automatically creates opportunities when status is `convert_to_opp`:
- **ID Format**: POT-XXXXXXXX (8 uppercase alphanumeric characters)
- **Auto-mapping**: Lead data is mapped to opportunity fields
- **Status Update**: Lead status becomes "Converted"

## Component Props

```javascript
<LeadChangeStatusModal
  leadId="string"           // Required: Lead ID to update
  initialLead={object}      // Optional: Initial lead data (avoids API call)
  isOpen={boolean}          // Required: Modal open state
  onClose={function}        // Required: Close callback
  onSuccess={function}      // Required: Success callback with updated lead
/>
```

## Integration Example

```javascript
import LeadChangeStatusModal from './components/LeadChangeStatusModal';

function LeadManagement() {
  const [statusModal, setStatusModal] = useState({
    isOpen: false,
    leadId: null,
    lead: null
  });

  const handleStatusChange = (lead) => {
    setStatusModal({
      isOpen: true,
      leadId: lead.id,
      lead: lead
    });
  };

  const handleStatusSuccess = (updatedLead) => {
    // Refresh your leads list
    refreshLeads();
    setStatusModal({ isOpen: false, leadId: null, lead: null });
  };

  return (
    <div>
      {/* Your leads list */}
      <button onClick={() => handleStatusChange(selectedLead)}>
        Change Status
      </button>

      <LeadChangeStatusModal
        leadId={statusModal.leadId}
        initialLead={statusModal.lead}
        isOpen={statusModal.isOpen}
        onClose={() => setStatusModal({ isOpen: false, leadId: null, lead: null })}
        onSuccess={handleStatusSuccess}
      />
    </div>
  );
}
```

## Behavior Decision: Modal Stays Open After Approval

**Decision**: The modal remains open after a lead is successfully approved.

**Reasoning**: 
- Better UX: Users can immediately convert approved leads without reopening the modal
- Workflow Efficiency: Common pattern is approve → convert in one session
- Clear Feedback: Status dropdown updates to show the new "Convert to Opportunity" option
- User Choice: Users can still close the modal if they don't want to convert immediately

**Alternative Considered**: Close modal after approval and require reopening for conversion
- **Rejected because**: Creates unnecessary friction and extra clicks for common workflow

## Accessibility Features

- **Keyboard Navigation**: Full tab order support
- **Focus Trapping**: Focus stays within modal when open
- **ESC Key**: Closes modal when pressed
- **Screen Reader Support**: Proper ARIA labels and descriptions
- **Focus Management**: Automatically focuses first interactive element
- **Visual Feedback**: Clear loading states and disabled states

## Toast Messages

- **Status Update**: "Lead status updated."
- **Conversion**: "Lead converted to Opportunity." with opportunity ID
- **Error Handling**: Specific error messages from API responses

## Test Scenario: Approve Then Convert

```javascript
// Test case: Full approve → convert workflow
describe('Lead Status Change: Approve → Convert', () => {
  it('should approve lead then allow conversion', async () => {
    // 1. Open modal with pending lead
    // 2. Select "approved" status
    // 3. Click "Update Status"
    // 4. Verify API call: POST /api/leads/123/status {"status": "approved"}
    // 5. Verify modal stays open
    // 6. Verify dropdown now includes "Convert to Opportunity"
    // 7. Select "convert_to_opp"
    // 8. Click "Update Status"
    // 9. Verify API call: POST /api/leads/123/status {"status": "convert_to_opp"}
    // 10. Verify opportunity ID format: POT-[A-Z0-9]{8}
    // 11. Verify toast messages appear
    // 12. Verify modal closes after conversion
  });
});
```

## Error Handling

- **Network Errors**: Shows toast with error message
- **API Errors**: Displays specific error details from server
- **Validation Errors**: Prevents invalid status transitions
- **Loading States**: Disables form during API calls

## Styling

- **Tailwind CSS**: Responsive, accessible design
- **Soft Rounded Corners**: Modern appearance
- **Proper Spacing**: Consistent padding and margins
- **Status Badges**: Color-coded status indicators
- **Loading Indicators**: Spinner animations during saves

## Dependencies

- React 18+
- axios (API calls)
- Tailwind CSS (styling)
- Radix UI components (accessible primitives)
- sonner (toast notifications)
- lucide-react (icons)

## File Structure

```
/components/
  LeadChangeStatusModal.js     # Main modal component
  ui/                          # Shadcn UI components
    dialog.js
    button.js
    select.js
    badge.js
    card.js
    label.js
```

## Backend Requirements

The backend must support:
1. Lead status change endpoint with opportunity conversion
2. Opportunity collection in MongoDB
3. Proper ID generation for opportunities (POT-XXXXXXXX format)
4. Audit trail logging for status changes

## Future Enhancements

- **Bulk Status Changes**: Select multiple leads for status updates
- **Custom Status Reasons**: Add reason field for rejections
- **Email Notifications**: Send notifications on status changes
- **Approval Workflows**: Multi-step approval processes
- **Status History**: Track all status changes with timestamps