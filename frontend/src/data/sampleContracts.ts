/**
 * frontend/src/data/sampleContracts.ts
 * Pre-loaded sample agreements for 1-click testing in the UI.
 */

export interface SampleContract {
  id: string;
  name: string;
  subtitle: string;
  tag: string;
  tagColor: string;
  filename: string;
  text: string;
}

export const SAMPLE_CONTRACTS: SampleContract[] = [
  {
    id: 'sample_a',
    name: 'Sample A: Fair Agreement',
    subtitle: 'Standard balanced 11-month residential lease with mutual notice.',
    tag: 'Balanced',
    tagColor: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20',
    filename: 'sample_a_fair.txt',
    text: `RESIDENTIAL LEASE AGREEMENT

This Residential Lease Agreement ("Agreement") is executed on this 1st day of November, 2026, at Bengaluru, Karnataka.

BETWEEN:
Mr. Anand Sharma, residing at #102, Palm Meadows, Whitefield, Bengaluru (hereinafter called the "Landlord", which expression shall include his legal heirs and assigns).
AND
Ms. Priya Nair, currently residing at #45, Richmond Road, Bengaluru (hereinafter called the "Tenant", which expression shall include her legal heirs and assigns).

1. Term of Tenancy
The tenancy shall be for an initial period of eleven (11) months commencing from 1st December 2026 to 31st October 2027.

2. Rent & Security Deposit
The tenant agrees to pay a monthly rent of Rs. 25,000/- (Rupees Twenty-Five Thousand only), payable on or before the 5th day of each calendar month. The tenant has deposited an interest-free refundable security deposit of Rs. 50,000/- (equivalent to two months' rent) with the Landlord.

3. Termination
Either party may terminate this agreement prior to the expiration of the term by providing thirty (30) days prior written notice to the other party.

4. Inspection and Entry
The Landlord or his authorized representative may enter and inspect the premises after giving at least twenty-four (24) hours prior written notice to the Tenant, during reasonable daytime hours.

5. Maintenance and Repairs
The Landlord shall be responsible for all major structural repairs and seepage issues. Minor day-to-day repairs, including replacement of bulbs and minor tap washers, shall be borne by the Tenant.

6. Utilities and Charges
The Tenant shall directly pay all electricity bills and piped gas charges as per meter readings during the subsistence of the tenancy.

7. Registration
This agreement shall be duly registered or notarized as required by applicable local tenancy practices, with costs shared equally between Landlord and Tenant.

IN WITNESS WHEREOF the parties have set their hands on the day and year first written above.
Landlord: [Signed: Anand Sharma]
Tenant: [Signed: Priya Nair]
Witness 1: Rajesh Rao
Witness 2: Kavita Menon
`
  },
  {
    id: 'sample_b',
    name: 'Sample B: Problematic Lease (Planted Contradictions)',
    subtitle: 'Contains 2 logical contradictions & 5 statutory violations under Indian law.',
    tag: '2 Contradictions / High Risk',
    tagColor: 'bg-rose-500/10 text-rose-600 border-rose-500/20',
    filename: 'sample_b_problematic.txt',
    text: `RESIDENTIAL TENANCY AGREEMENT

This Agreement is made on 15th October 2026 at Koramangala, Bengaluru, Karnataka.

BETWEEN:
Mr. Vikram Malhotra ("Landlord")
AND
Mr. Rahul Verma ("Tenant")

1. Term of Lease
The tenancy shall commence on 1st November 2026 and continue for a period of 24 months.

2. Monthly Rent and Escalation
The monthly rent shall be Rs. 40,000/- payable in advance. The Landlord reserves the absolute right to escalate the monthly rent by 20% at any time without prior written notice.

3. Tenant Early Termination Right
The Tenant may terminate this tenancy at any time by giving thirty (30) days prior written notice to the Landlord.

4. Security Deposit
The Tenant shall deposit a refundable security deposit of Rs. 4,00,000/- (equivalent to ten months' rent) with the Landlord upon execution of this deed.

5. Landlord Unrestricted Inspection
The Landlord and his agents shall have the right to enter and inspect the premises at any hour of the day or night without any prior notice to the Tenant.

6. Maintenance Responsibility
All repairs whatsoever, including structural leaks, external wall cracks, and roof maintenance, shall be the sole and exclusive financial responsibility of the Tenant.

7. Permission to Keep Companion Pets
The Tenant is expressly permitted to keep domestic companion pets (including one dog or cat) within the leased premises, provided they cause no nuisance.

8. Utility Disconnection Remedy
In the event of any delay in rent payment exceeding five (5) days, the Landlord shall have the absolute right to disconnect the electricity and water supply to the premises without judicial intervention.

9. Late Fee Penalties
Any payment received after the due date shall attract a penalty interest of 10% per week on the outstanding rent.

10. Subletting Prohibition
The Tenant shall not sublet, assign, or part with possession of any part of the premises without written consent.

11. Lock-in Period
The first twelve (12) months shall be considered a mandatory lock-in period. If the Tenant vacates during this period, the entire rent for the remaining lock-in period shall be forfeited.

12. Absolute Termination Restriction
Early termination by the Tenant is strictly prohibited unless at least ninety (90) days prior written notice is served. Any notice of less than ninety days shall be null and void.

13. Forfeiture of Entire Security Deposit
If the Tenant commits any breach of house rules, the Landlord shall be entitled to forfeit the whole security deposit of Rs. 4,00,000/- as liquidated damages.

14. Renewal and Stamp Duty
Any renewal shall be at the sole discretion of the Landlord. All registration and stamp duty costs shall be borne exclusively by the Tenant.

15. Notice Service
All notices under this agreement shall be delivered by registered post to the addresses mentioned herein.

16. Total Pet Prohibition
Under no circumstances whatsoever shall any animals, birds, or domestic pets be brought or maintained inside the premises. Keeping any pet shall constitute immediate breach of lease.

IN WITNESS WHEREOF the parties have affixed their signatures.
Landlord: [Signed: Vikram Malhotra]
Tenant: [Signed: Rahul Verma]
`
  },
  {
    id: 'sample_c',
    name: 'Sample C: Messy Real-World Agreement',
    subtitle: 'Mixed numbering, roman numerals, uppercase clauses, and noisy formatting.',
    tag: 'Messy Layout',
    tagColor: 'bg-amber-500/10 text-amber-600 border-amber-500/20',
    filename: 'sample_c_messy.txt',
    text: `RENTAL AGREEMENT / LEASE MEMORANDUM
DRAFTED ON 10/12/2026 AT HYDERABAD TELANGANA

PARTIES:
LESSOR: SRI K. VENKATESHWARLU, S/O LATE K. NARAYANA, AGED 58 YEARS, HYDERABAD
LESSEE: SMT. ANANYA REDDY, D/O M. REDDY, AGED 29 YEARS, HYDERABAD

THE HOUSE PROPERTY BEARING NO. 8-2-293/82/A, JUBILEE HILLS, HYDERABAD

TERMS AND COVENANTS:

1. DURATION:
THE LEASE SHALL BE VALID FOR ELEVEN MONTHS COMMENCING FROM
DECEMBER 1ST 2026 UNTIL OCTOBER 31ST 2027.

Clause II. RENT PAYMENT:
The tenant agrees to pay Rs 35000/- (Thirty Five Thousand Rupees)
every month within 7 days of due date by online transfer.

(3) SECURITY ADVANCE:
An amount of Rs 70000 (Two months rent) is paid by tenant
as interest free refundable deposit.

Fourth: TERMINATION TERMS:
Either party can give one month notice to vacate the premises
or one month rent in lieu of notice period.

Clause 5: INSPECTION OF PREMISES:
The lessor may enter the rented premises for inspection
only after giving 24 hours prior written notice to the lessee during daytime.

6: ELECTRICITY BILLS:
Tenant shall pay all electricity bills as per TSSPDCL power meter reading
regularly without delay.

(7) REPAIRS:
Minor repairs up to Rs 1000 will be borne by the tenant.
All major structural seepages and plumbing issues shall be fixed by the landlord.

Clause 8: DEPOSIT REFUND:
The landlord shall refund the entire security deposit of Rs 70000
within thirty (30) days from the date the tenant surrenders physical possession.

IN WITNESS WHEREOF THE PARTIES HAVE EXECUTED THIS DEED.
LESSOR: K. VENKATESHWARLU
LESSEE: ANANYA REDDY
WITNESSES:
1. G. SURESH
2. P. RAMESH
`
  }
];
