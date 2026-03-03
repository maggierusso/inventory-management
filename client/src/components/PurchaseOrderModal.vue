<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{
                mode === "create"
                  ? t("purchaseOrder.createTitle")
                  : t("purchaseOrder.viewTitle")
              }}
            </h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path
                  d="M15 5L5 15M5 5L15 15"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                />
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <!-- For Item info -->
            <div class="for-item-banner">
              <span class="for-item-label"
                >{{ t("purchaseOrder.forItem") }}:</span
              >
              <span class="for-item-name">{{ backlogItem.item_name }}</span>
              <span class="for-item-sku">{{ backlogItem.item_sku }}</span>
            </div>

            <!-- Create Mode: Form -->
            <template v-if="mode === 'create'">
              <div v-if="formError" class="form-error">{{ formError }}</div>
              <form @submit.prevent="submitForm" class="po-form">
                <div class="form-group">
                  <label class="form-label">{{
                    t("purchaseOrder.supplierName")
                  }}</label>
                  <input
                    v-model="form.supplier_name"
                    type="text"
                    class="form-input"
                    :placeholder="t('purchaseOrder.supplierPlaceholder')"
                    required
                  />
                </div>

                <div class="form-row">
                  <div class="form-group">
                    <label class="form-label">{{
                      t("purchaseOrder.quantity")
                    }}</label>
                    <input
                      v-model.number="form.quantity"
                      type="number"
                      class="form-input"
                      min="1"
                      required
                    />
                  </div>

                  <div class="form-group">
                    <label class="form-label">{{
                      t("purchaseOrder.unitCost")
                    }}</label>
                    <input
                      v-model.number="form.unit_cost"
                      type="number"
                      class="form-input"
                      step="0.01"
                      min="0"
                      required
                    />
                  </div>
                </div>

                <div class="form-group total-cost-display">
                  <span class="total-cost-label"
                    >{{ t("purchaseOrder.totalCost") }}:</span
                  >
                  <span class="total-cost-value"
                    >{{ currencySymbol }}{{ totalCost }}</span
                  >
                </div>

                <div class="form-group">
                  <label class="form-label">{{
                    t("purchaseOrder.expectedDelivery")
                  }}</label>
                  <input
                    v-model="form.expected_delivery_date"
                    type="date"
                    class="form-input"
                    required
                  />
                </div>

                <div class="form-group">
                  <label class="form-label">{{
                    t("purchaseOrder.notes")
                  }}</label>
                  <textarea
                    v-model="form.notes"
                    class="form-textarea"
                    :placeholder="t('purchaseOrder.notesPlaceholder')"
                    rows="3"
                  ></textarea>
                </div>
              </form>
            </template>

            <!-- View Mode: Read-only display -->
            <template v-else>
              <div v-if="poLoading" class="po-loading">
                {{ t("common.loading") }}
              </div>
              <div v-else-if="poError" class="form-error">{{ poError }}</div>
              <div v-else-if="purchaseOrder" class="po-details">
                <div class="info-grid">
                  <div class="info-item">
                    <div class="info-label">{{ t("purchaseOrder.poId") }}</div>
                    <div class="info-value po-id">{{ purchaseOrder.id }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">
                      {{ t("purchaseOrder.status") }}
                    </div>
                    <div class="info-value">
                      <span class="badge info">{{ purchaseOrder.status }}</span>
                    </div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">
                      {{ t("purchaseOrder.supplierName") }}
                    </div>
                    <div class="info-value">
                      {{ purchaseOrder.supplier_name }}
                    </div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">
                      {{ t("purchaseOrder.quantity") }}
                    </div>
                    <div class="info-value">{{ purchaseOrder.quantity }}</div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">
                      {{ t("purchaseOrder.unitCost") }}
                    </div>
                    <div class="info-value">
                      {{ currencySymbol }}{{ purchaseOrder.unit_cost }}
                    </div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">
                      {{ t("purchaseOrder.totalCost") }}
                    </div>
                    <div class="info-value total-cost-value">
                      {{ currencySymbol
                      }}{{
                        (
                          purchaseOrder.quantity * purchaseOrder.unit_cost
                        ).toFixed(2)
                      }}
                    </div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">
                      {{ t("purchaseOrder.expectedDelivery") }}
                    </div>
                    <div class="info-value">
                      {{ formatDate(purchaseOrder.expected_delivery_date) }}
                    </div>
                  </div>
                  <div class="info-item">
                    <div class="info-label">
                      {{ t("purchaseOrder.createdDate") }}
                    </div>
                    <div class="info-value">
                      {{ formatDate(purchaseOrder.created_date) }}
                    </div>
                  </div>
                  <div v-if="purchaseOrder.notes" class="info-item full-width">
                    <div class="info-label">{{ t("purchaseOrder.notes") }}</div>
                    <div class="info-value">{{ purchaseOrder.notes }}</div>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">
              {{ t("common.close") }}
            </button>
            <button
              v-if="mode === 'create'"
              class="btn-primary"
              :disabled="submitting"
              @click="submitForm"
            >
              {{ submitting ? t("common.loading") : t("purchaseOrder.create") }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, computed, watch } from "vue";
import { useI18n } from "../composables/useI18n";
import { api } from "../api";

export default {
  name: "PurchaseOrderModal",
  props: {
    isOpen: {
      type: Boolean,
      default: false,
    },
    backlogItem: {
      type: Object,
      default: null,
    },
    mode: {
      type: String,
      default: "create",
    },
  },
  emits: ["close", "po-created"],
  setup(props, { emit }) {
    const { t, currentCurrency } = useI18n();

    const currencySymbol = computed(() =>
      currentCurrency.value === "JPY" ? "¥" : "$",
    );

    // Create mode state
    const form = ref({
      supplier_name: "",
      quantity: 0,
      unit_cost: 0,
      expected_delivery_date: "",
      notes: "",
    });
    const formError = ref(null);
    const submitting = ref(false);

    // View mode state
    const purchaseOrder = ref(null);
    const poLoading = ref(false);
    const poError = ref(null);

    const totalCost = computed(() => {
      const qty = Number(form.value.quantity) || 0;
      const cost = Number(form.value.unit_cost) || 0;
      return (qty * cost).toFixed(2);
    });

    const resetForm = () => {
      if (props.backlogItem) {
        const shortage =
          (props.backlogItem.quantity_needed || 0) -
          (props.backlogItem.quantity_available || 0);
        form.value = {
          supplier_name: "",
          quantity: shortage > 0 ? shortage : 1,
          unit_cost: 0,
          expected_delivery_date: "",
          notes: "",
        };
      } else {
        form.value = {
          supplier_name: "",
          quantity: 1,
          unit_cost: 0,
          expected_delivery_date: "",
          notes: "",
        };
      }
      formError.value = null;
      submitting.value = false;
    };

    const fetchPurchaseOrder = async () => {
      if (!props.backlogItem) return;
      poLoading.value = true;
      poError.value = null;
      purchaseOrder.value = null;
      try {
        purchaseOrder.value = await api.getPurchaseOrderByBacklogItem(
          props.backlogItem.id,
        );
      } catch (err) {
        poError.value =
          err.response && err.response.status === 404
            ? "No purchase order found for this item."
            : "Failed to load purchase order.";
      } finally {
        poLoading.value = false;
      }
    };

    watch(
      () => props.isOpen,
      (val) => {
        if (val) {
          if (props.mode === "create") {
            resetForm();
          } else {
            fetchPurchaseOrder();
          }
        } else {
          resetForm();
          purchaseOrder.value = null;
          poError.value = null;
        }
      },
    );

    watch(
      () => props.mode,
      (val) => {
        if (props.isOpen) {
          if (val === "create") {
            resetForm();
          } else {
            fetchPurchaseOrder();
          }
        }
      },
    );

    const submitForm = async () => {
      if (!props.backlogItem) return;
      formError.value = null;
      submitting.value = true;
      try {
        const payload = {
          backlog_item_id: props.backlogItem.id,
          supplier_name: form.value.supplier_name,
          quantity: form.value.quantity,
          unit_cost: form.value.unit_cost,
          expected_delivery_date: form.value.expected_delivery_date,
          notes: form.value.notes || "",
        };
        const newPO = await api.createPurchaseOrder(payload);
        emit("po-created", newPO);
        emit("close");
      } catch (err) {
        formError.value =
          err.response?.data?.detail || "Failed to create purchase order.";
      } finally {
        submitting.value = false;
      }
    };

    const close = () => {
      emit("close");
    };

    const formatDate = (dateString) => {
      if (!dateString) return "N/A";
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return dateString;
      return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
      });
    };

    return {
      t,
      currencySymbol,
      form,
      formError,
      submitting,
      totalCost,
      purchaseOrder,
      poLoading,
      poError,
      submitForm,
      close,
      formatDate,
    };
  },
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.close-button:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.for-item-banner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.for-item-label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.for-item-name {
  font-size: 0.938rem;
  font-weight: 600;
  color: #0f172a;
}

.for-item-sku {
  font-size: 0.813rem;
  color: #2563eb;
  font-family: "Monaco", "Courier New", monospace;
}

.po-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.form-input {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  font-size: 0.938rem;
  color: #0f172a;
  font-family: inherit;
  outline: none;
  transition: border-color 0.15s ease;
}

.form-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-textarea {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 0.5rem 0.75rem;
  font-size: 0.938rem;
  color: #0f172a;
  font-family: inherit;
  outline: none;
  resize: vertical;
  transition: border-color 0.15s ease;
}

.form-textarea:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.total-cost-display {
  flex-direction: row;
  align-items: center;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem 1rem;
}

.total-cost-label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-right: 0.5rem;
}

.total-cost-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #2563eb;
}

.form-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.po-loading {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

.po-details {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.info-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 500;
}

.info-value.po-id {
  font-family: "Monaco", "Courier New", monospace;
  color: #2563eb;
}

.info-value.total-cost-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #2563eb;
}

.badge {
  display: inline-block;
  padding: 0.313rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.info {
  background: #dbeafe;
  color: #1e40af;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-secondary {
  padding: 0.625rem 1.25rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.btn-primary {
  padding: 0.625rem 1.25rem;
  background: #2563eb;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
