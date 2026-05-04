<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'

const API_BASE = (import.meta.env.VITE_API_URL || '/api/v1').replace(/\/$/, '')

const tenants = [
  { id: 'tenant_a', name: 'Tenant A - Campus Budget Travel' },
  { id: 'tenant_b', name: 'Tenant B - City Explorer Agency' },
]

const form = reactive({
  tenant_id: 'tenant_a',
  from_code: 'SFO',
  to_code: 'LON',
  location: 'London',
  depart_date: '2026-05-01',
  check_in: '2026-05-01',
  check_out: '2026-05-06',
  budget: 1500,
})

const currentTenant = computed(() => tenants.find(t => t.id === form.tenant_id) || tenants[0])
const tenantShortName = computed(() => currentTenant.value.name.replace(/^Tenant [AB] - /, ''))

watch(() => form.tenant_id, (id) => {
  document.body.classList.toggle('tenant-b', id === 'tenant_b')
}, { immediate: true })

const loading = ref(false)
const saving = ref(false)
const error = ref('')
const success = ref('')
const response = ref(null)
const verifiedBooking = ref(null)
const demoUsers = reactive({})
const selected = reactive({ flightId: '', hotelId: '', attractionIds: [] })

const flights = computed(() => response.value?.flights || [])
const hotels = computed(() => response.value?.hotels || [])
const attractions = computed(() => response.value?.attractions || [])
const results = computed(() => response.value?.results || [])
const nights = computed(() => response.value?.nights || getNights())
const selectedFlight = computed(() => flights.value.find((f) => f.id === selected.flightId) || flights.value[0] || null)
const selectedHotel = computed(() => hotels.value.find((h) => h.id === selected.hotelId) || hotels.value[0] || null)
const selectedAttractions = computed(() => attractions.value.filter((a) => selected.attractionIds.includes(a.id)))
const flightCost = computed(() => Number(selectedFlight.value?.price || 0))
const stayCost = computed(() => Number(selectedHotel.value?.price_per_night || 0) * nights.value)
const activityCost = computed(() => selectedAttractions.value.reduce((sum, a) => sum + Number(a.price || 0), 0))
const totalCost = computed(() => flightCost.value + stayCost.value + activityCost.value)
const remaining = computed(() => Number(form.budget || 0) - totalCost.value)
const isOverBudget = computed(() => totalCost.value > Number(form.budget || 0))
const canBook = computed(() => Boolean(selectedFlight.value && selectedHotel.value))

function getNights() {
  const start = new Date(`${form.check_in}T00:00:00`)
  const end = new Date(`${form.check_out}T00:00:00`)
  const diff = Math.round((end - start) / 86400000)
  return Number.isFinite(diff) && diff > 0 ? diff : 1
}

function money(value) {
  return Number(value || 0).toLocaleString('en-US', { style: 'currency', currency: 'USD' })
}

function airportCode(value) {
  return String(value || 'TBD').replace('.AIRPORT', '').replace('.CITY', '').slice(0, 3).toUpperCase()
}

function defaultSelection(payload) {
  const cheapest = payload.results?.[0]
  selected.flightId = cheapest?.flight?.id || payload.flights?.[0]?.id || ''
  selected.hotelId = cheapest?.hotel?.id || payload.hotels?.[0]?.id || ''
  selected.attractionIds = cheapest?.attractions?.map((a) => a.id) || []
}

async function ensureUser() {
  if (demoUsers[form.tenant_id]) return demoUsers[form.tenant_id]
  const res = await fetch(`${API_BASE}/setup-seed-data/?tenant_id=${encodeURIComponent(form.tenant_id)}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || 'Demo user setup failed')
  demoUsers[form.tenant_id] = data.user_id
  return data.user_id
}

async function searchTrips() {
  loading.value = true
  error.value = ''
  success.value = ''
  verifiedBooking.value = null
  const params = new URLSearchParams({
    tenant_id: form.tenant_id,
    from_code: form.from_code,
    to_code: form.to_code,
    location: form.location || form.to_code,
    depart_date: form.depart_date,
    check_in: form.check_in,
    check_out: form.check_out,
    budget: String(form.budget || 0),
    limit: '50',
  })
  try {
    const res = await fetch(`${API_BASE}/trips/search?${params}`, { headers: { 'X-Tenant-ID': form.tenant_id } })
    const payload = await res.json()
    if (!res.ok) throw new Error(payload.detail || 'Trip search failed')
    response.value = payload
    defaultSelection(payload)
  } catch (err) {
    response.value = null
    error.value = err instanceof Error ? err.message : 'Backend is not reachable'
  } finally {
    loading.value = false
  }
}

function usePlan(plan) {
  selected.flightId = plan.flight.id
  selected.hotelId = plan.hotel.id
  selected.attractionIds = plan.attractions.map((a) => a.id)
  success.value = ''
  verifiedBooking.value = null
}

function activeTrip(plan = null) {
  return plan || { flight: selectedFlight.value, hotel: selectedHotel.value, attractions: selectedAttractions.value }
}

function bookingPayload(plan = null, userId = 1) {
  const trip = activeTrip(plan)
  return {
    User_Id: userId,
    Tenant_Id: form.tenant_id,
    Agent_Id: null,
    Start_Date: form.depart_date,
    End_Date: form.check_out,
    hotel_reservations: [{
      Hotel_Code: Number(trip.hotel.hotel_code || 1),
      Check_In_Date: form.check_in,
      Check_In_Time: '15:00',
      Check_Out_Date: form.check_out,
      Check_Out_Time: '11:00',
      Rate: Number(trip.hotel.price_per_night || 0),
    }],
    flight_reservations: [{
      Airline_Code: trip.flight.airline_code || 'NA',
      Flight_Number: trip.flight.flight_number || trip.flight.id || 'TBD',
      Departure_Date: trip.flight.depart_date || form.depart_date,
      Departure_Time: trip.flight.departure_time || '09:00',
      Arrive_Date: trip.flight.depart_date || form.depart_date,
      Arrive_Time: trip.flight.arrival_time || '17:00',
      Rate: Number(trip.flight.price || 0),
      Origin_Airport_Code: trip.flight.from_airport_code || airportCode(form.from_code),
      Destination_Airport_Code: trip.flight.to_airport_code || airportCode(form.to_code),
    }],
    activity_reservations: trip.attractions.map((a) => ({
      Activity_Name: a.name,
      Location: a.location,
      Activity_Date: form.depart_date,
      Price: Number(a.price || 0),
    })),
  }
}

async function bookTrip(plan = null) {
  const trip = activeTrip(plan)
  if (!trip.flight || !trip.hotel) return
  saving.value = true
  error.value = ''
  success.value = ''
  try {
    const userId = await ensureUser()
    const createRes = await fetch(`${API_BASE}/bookings/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(bookingPayload(plan, userId)),
    })
    const created = await createRes.json()
    if (!createRes.ok) throw new Error(created.detail || 'Booking save failed')
    const verifyRes = await fetch(`${API_BASE}/bookings/${created.Booking_Id}`)
    const verified = await verifyRes.json()
    if (!verifyRes.ok) throw new Error(verified.detail || 'Booking verification failed')
    verifiedBooking.value = verified
    success.value = `Saved booking #${verified.Booking_Id} and verified DB persistence. Total: ${money(verified.total_cost)}.`
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Booking failed'
  } finally {
    saving.value = false
  }
}

onMounted(searchTrips)
</script>

<template>
  <main class="app-shell">
    <section class="hero-card">
      <div>
        <div class="tenant-badge"><span class="tenant-badge-dot"></span>{{ tenantShortName }}</div>
        <p class="eyebrow">ThriftyBackpacker Phase 2</p>
        <h1>Plan a London trip under a student budget.</h1>
        <p class="hero-copy">The UI now consumes the backend, combines flights + hostels + activities, filters by budget, sorts cheapest first, warns on overspending, and saves bookings.</p>
      </div>
      <div class="phase-badges"><span>Budget filter</span><span>Total cost</span><span>Cheapest first</span><span>Tenant pricing</span><span>Booking DB</span></div>
    </section>

    <section class="panel">
      <div class="section-heading"><div><p class="eyebrow">Search</p><h2>Trip details</h2></div><button class="primary-button" type="button" :disabled="loading" @click="searchTrips">{{ loading ? 'Searching...' : 'Search trips' }}</button></div>
      <form class="search-grid" @submit.prevent="searchTrips">
        <label>Travel agency tenant<select v-model="form.tenant_id"><option v-for="tenant in tenants" :key="tenant.id" :value="tenant.id">{{ tenant.name }}</option></select></label>
        <label>Budget<input v-model.number="form.budget" min="0" type="number" /></label>
        <label>From<input v-model.trim="form.from_code" placeholder="SFO" /></label>
        <label>To<input v-model.trim="form.to_code" placeholder="LON" /></label>
        <label>Destination<input v-model.trim="form.location" placeholder="London" /></label>
        <label>Depart<input v-model="form.depart_date" type="date" /></label>
        <label>Check in<input v-model="form.check_in" type="date" /></label>
        <label>Check out<input v-model="form.check_out" type="date" /></label>
      </form>
    </section>

    <p v-if="error" class="alert error">{{ error }}</p>
    <p v-if="success" class="alert success">{{ success }}</p>
    <p v-if="response" class="alert" :class="results.length ? 'success' : 'warning'">{{ response.message }}</p>

    <section v-if="response" class="summary-grid">
      <article class="summary-card"><span>Tenant</span><strong>{{ response.tenant_name }}</strong></article>
      <article class="summary-card"><span>Budget</span><strong>{{ money(response.budget) }}</strong></article>
      <article class="summary-card"><span>Nights</span><strong>{{ nights }}</strong></article>
      <article class="summary-card"><span>Results</span><strong>{{ results.length }}</strong></article>
      <article class="summary-card highlight"><span>Selected total</span><strong>{{ money(totalCost) }}</strong></article>
    </section>

    <section v-if="response" class="panel builder-panel">
      <div class="section-heading">
        <div><p class="eyebrow">Real-time builder</p><h2>Customize selected trip</h2></div>
        <div class="builder-total" :class="isOverBudget ? 'danger' : ''"><span>Total</span><strong>{{ money(totalCost) }}</strong></div>
      </div>
      <div class="builder-grid">
        <label>Flight<select v-model="selected.flightId"><option v-for="flight in flights" :key="flight.id" :value="flight.id">{{ flight.airline }} {{ flight.flight_number }} - {{ money(flight.price) }} - {{ flight.duration }}</option></select></label>
        <label>Hostel<select v-model="selected.hotelId"><option v-for="hotel in hotels" :key="hotel.id" :value="hotel.id">{{ hotel.name }} - {{ money(hotel.price_per_night) }}/night</option></select></label>
        <div><p class="muted">Activities</p><label v-for="activity in attractions" :key="activity.id"><span><input v-model="selected.attractionIds" type="checkbox" :value="activity.id" /> {{ activity.name }} ({{ money(activity.price) }})</span></label></div>
      </div>
      <div class="budget-status" :class="isOverBudget ? 'danger' : 'good'"><strong>{{ isOverBudget ? 'Budget Alert: selection exceeds budget.' : `Within budget: ${money(remaining)} remaining.` }}</strong><span>{{ money(flightCost) }} flight + {{ money(stayCost) }} stay + {{ money(activityCost) }} activities</span></div>
      <button class="primary-button" type="button" :disabled="saving || !canBook" @click="bookTrip()">{{ saving ? 'Saving...' : 'Book selected trip' }}</button>
    </section>

    <section class="panel">
      <div class="section-heading"><div><p class="eyebrow">Sorted output</p><h2>Cheapest complete plans first</h2></div></div>
      <div v-if="!results.length" class="empty-state">No results available for this budget.</div>
      <div v-else class="trip-list">
        <article v-for="(plan, index) in results" :key="plan.id" class="trip-card">
          <div class="trip-card-header"><h3>#{{ index + 1 }} {{ money(plan.total_cost) }}</h3><span class="remaining">{{ money(plan.budget_remaining) }} left</span></div>
          <dl class="trip-details">
            <div><dt>Flight</dt><dd>{{ plan.flight.airline }} {{ plan.flight.flight_number }} · {{ plan.flight.duration }}</dd></div>
            <div><dt>Stay</dt><dd>{{ plan.hotel.name }} · {{ plan.nights }} nights</dd></div>
            <div><dt>Activity</dt><dd>{{ plan.attractions.map((a) => a.name).join(', ') }}</dd></div>
            <div><dt>Formula</dt><dd>{{ plan.formula }}</dd></div>
          </dl>
          <div class="trip-actions"><button class="secondary-button" type="button" @click="usePlan(plan)">Use plan</button><button class="primary-button small" type="button" :disabled="saving" @click="bookTrip(plan)">Book</button></div>
        </article>
      </div>
    </section>

    <section v-if="verifiedBooking" class="panel">
      <p class="eyebrow">Database verification</p>
      <h2>Saved booking #{{ verifiedBooking.Booking_Id }}</h2>
      <p>User: {{ verifiedBooking.user.First_Name }} {{ verifiedBooking.user.Last_Name }} · Persisted total: {{ money(verifiedBooking.total_cost) }} · Activities stored: {{ verifiedBooking.activity_reservations.length }}</p>
    </section>
  </main>
</template>
