// ============================================================================
// APB Monitor
// ============================================================================
// Observe le bus APB et capture les transactions
// Envoie les transactions au scoreboard via analysis_port
// ============================================================================

class apb_monitor extends uvm_monitor;

    // =========================================================================
    // Enregistrement UVM
    // =========================================================================
    `uvm_component_utils(apb_monitor)

    // =========================================================================
    // Interface virtuelle
    // =========================================================================
    virtual apb_if vif;

    // =========================================================================
    // Analysis Port - Pour envoyer les transactions au scoreboard
    // =========================================================================
    uvm_analysis_port #(apb_seq_item) analysis_port;

    // =========================================================================
    // Constructeur
    // =========================================================================
    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    // =========================================================================
    // Build Phase
    // =========================================================================
    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        // Créer l'analysis port
        analysis_port = new("analysis_port", this);

        // Récupérer l'interface
        if (!uvm_config_db#(virtual apb_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("NOVIF", "Virtual interface not found")
        end
    endfunction

    // =========================================================================
    // Run Phase - Observer le bus
    // =========================================================================
    virtual task run_phase(uvm_phase phase);
        apb_seq_item txn;

        // Attendre la fin du reset
        @(posedge vif.preset_n);

        forever begin
            // TODO 1: Détecter le début d'une transaction
            // Une transaction commence quand PSEL=1 et PENABLE=0 (phase SETUP)
            @(posedge vif.pclk);

            if (vif.monitor_cb.psel && !vif.monitor_cb.penable) begin
                // Créer une nouvelle transaction
                txn = apb_seq_item::type_id::create("txn");

                // TODO 2: Capturer les informations de la phase SETUP
                txn.addr  = vif.monitor_cb.paddr;
                txn.write = vif.monitor_cb.pwrite;
                txn.wdata = vif.monitor_cb.pwdata;

                // TODO 3: Attendre la fin de la phase ACCESS
                // Le transfert est complété quand PSEL=1, PENABLE=1, PREADY=1
                @(posedge vif.pclk);  // Passage en ACCESS

                while (!(vif.monitor_cb.psel && vif.monitor_cb.penable && vif.monitor_cb.pready)) begin
                    @(posedge vif.pclk);
                end

                // TODO 4: Capturer les données de lecture et l'erreur
                txn.rdata  = vif.monitor_cb.prdata;
                txn.slverr = vif.monitor_cb.pslverr;

                // TODO 5: Envoyer la transaction au scoreboard
                // Utilise: analysis_port.write(txn)
                analysis_port.write(txn);

                `uvm_info(get_name(), $sformatf("Observed: %s", txn.convert2string()), UVM_MEDIUM)
            end
        end
    endtask

endclass
