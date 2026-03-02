<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Review AI-generated restock recommendations and submit purchase orders within budget.</p>
    </div>

    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Budget Control Card -->
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">Budget Control</h3>
        </div>
        <div class="budget-controls">
          <div class="slider-row">
            <label class="slider-label" for="budget-slider">Budget</label>
            <input
              id="budget-slider"
              type="range"
              min="500"
              max="50000"
              step="500"
              v-model.number="budget"
              class="budget-slider"
            />
            <span class="budget-display">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
          </div>
          <div class="budget-summary" v-if="restockResponse">
            <div class="budget-stat">
              <span class="budget-stat-label">Spent</span>
              <span class="budget-stat-value spent">{{ currencySymbol }}{{ restockResponse.spent.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</span>
            </div>
            <div class="budget-divider"></div>
            <div class="budget-stat">
              <span class="budget-stat-label">Remaining</span>
              <span class="budget-stat-value remaining">{{ currencySymbol }}{{ restockResponse.remaining.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Success message after order submission -->
      <div v-if="successMessage" class="success-banner">
        {{ successMessage }}
      </div>

      <!-- Recommendations Table Card -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            Recommendations
            <span v-if="recommendations.length" class="count-badge">{{ recommendations.length }}</span>
          </h3>
          <button
            class="btn-primary"
            :disabled="!recommendations.length || submitting"
            @click="placeOrder"
          >
            {{ submitting ? 'Submitting...' : 'Place Order' }}
          </button>
        </div>

        <div v-if="!recommendations.length" class="empty-state">
          No recommendations available for the current budget.
        </div>
        <div v-else class="table-container">
          <table class="restock-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Name</th>
                <th>Category</th>
                <th>Trend</th>
                <th class="col-num">Qty</th>
                <th class="col-num">Unit Cost</th>
                <th class="col-num">Line Total</th>
                <th class="col-num">Lead Time</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ item.name }}</td>
                <td>{{ item.category }}</td>
                <td>
                  <span :class="['badge', item.trend]">{{ item.trend }}</span>
                </td>
                <td class="col-num">{{ item.quantity }}</td>
                <td class="col-num">{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</td>
                <td class="col-num"><strong>{{ currencySymbol }}{{ item.line_total.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</strong></td>
                <td class="col-num">{{ item.lead_time_days }}d</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const budget = ref(5000)
    const restockResponse = ref(null)
    const loading = ref(true)
    const submitting = ref(false)
    const error = ref(null)
    const successMessage = ref(null)

    // Derived from restockResponse for convenience
    const recommendations = computed(() => {
      return restockResponse.value ? restockResponse.value.recommendations : []
    })

    const loadRecommendations = async () => {
      error.value = null
      loading.value = true
      try {
        restockResponse.value = await api.getRestockRecommendations(budget.value)
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Debounce timer ref — avoids hammering the API on every slider tick
    let debounceTimer = null

    const debouncedLoad = () => {
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendations()
      }, 300)
    }

    // Watch budget slider and re-fetch with debounce
    watch(budget, () => {
      debouncedLoad()
    })

    const placeOrder = async () => {
      if (!recommendations.value.length || submitting.value) return

      submitting.value = true
      successMessage.value = null
      error.value = null

      try {
        const savedOrder = await api.submitRestockOrder({
          budget: budget.value,
          items: recommendations.value
        })

        successMessage.value = `Order ${savedOrder.id} submitted successfully. Expected delivery: ${savedOrder.expected_delivery}.`

        // Clear recommendations after a successful submission
        restockResponse.value = {
          ...restockResponse.value,
          recommendations: [],
          spent: restockResponse.value.spent,
          remaining: restockResponse.value.remaining
        }
      } catch (err) {
        error.value = 'Failed to submit order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      currencySymbol,
      budget,
      restockResponse,
      recommendations,
      loading,
      submitting,
      error,
      successMessage,
      placeOrder
    }
  }
}
</script>

<style scoped>
.restocking {
  /* inherits global .main-content padding */
}

/* Budget card */
.budget-card {
  margin-bottom: 1.25rem;
}

.budget-controls {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.slider-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
  min-width: 48px;
}

.budget-slider {
  flex: 1;
  accent-color: #2563eb;
  height: 6px;
  cursor: pointer;
}

.budget-display {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  min-width: 100px;
  text-align: right;
}

.budget-summary {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 0.875rem 1.25rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.budget-stat {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.budget-stat-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.budget-stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.budget-stat-value.spent {
  color: #ea580c;
}

.budget-stat-value.remaining {
  color: #059669;
}

.budget-divider {
  width: 1px;
  height: 36px;
  background: #e2e8f0;
}

/* Success banner */
.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 0.875rem 1.25rem;
  border-radius: 8px;
  margin-bottom: 1.25rem;
  font-size: 0.938rem;
  font-weight: 500;
}

/* Place Order button */
.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.625rem 1.5rem;
  border-radius: 6px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

/* Count badge next to card title */
.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #e0e7ff;
  color: #3730a3;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.125rem 0.5rem;
  border-radius: 999px;
  margin-left: 0.5rem;
  letter-spacing: 0;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 2.5rem 1rem;
  color: #64748b;
  font-size: 0.938rem;
}

/* Table */
.restock-table {
  width: 100%;
  border-collapse: collapse;
}

.col-num {
  text-align: right;
  width: 110px;
}
</style>
