// ============================================================================
// APB Driver
// ============================================================================
// Convertit les transactions APB en signaux sur le bus
// Implémente le protocole APB (SETUP + ACCESS phases)
// ============================================================================

class apb_driver extends uvm_driver #(apb_seq_item);

    // =========================================================================
    // Enregistrement UVM
    // =========================================================================
    `uvm_component_utils(apb_driver)

    // =========================================================================
    // Interface virtuelle
    // =========================================================================
    // En UVM, on utilise une interface "virtuelle" pour accéder aux signaux
    virtual apb_if vif;

    // =========================================================================
    // Constructeur
    // =========================================================================
    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    // =========================================================================
    // Build Phase - Récupérer l'interface
    // =========================================================================
    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        // Récupérer l'interface depuis la config DB
        if (!uvm_config_db#(virtual apb_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("NOVIF", "Virtual interface not found in config_db")
        end
    endfunction

    // =========================================================================
    // Run Phase - Boucle principale du driver
    // =========================================================================
    virtual task run_phase(uvm_phase phase);
        // Attendre la fin du reset
        @(posedge vif.preset_n);
        @(posedge vif.pclk);

        forever begin
            // TODO 1: Récupérer la prochaine transaction de la séquence
            // Utilise: seq_item_port.get_next_item(req)
            seq_item_port.get_next_item(req);

            // Exécuter la transaction
            drive_transaction(req);

            // TODO 2: Signaler que la transaction est terminée
            // Utilise: seq_item_port.item_done()
            seq_item_port.item_done();
        end
    endtask

    // =========================================================================
    // TODO 3: Implémenter le protocole APB
    // =========================================================================
    virtual task drive_transaction(apb_seq_item txn);

        // -----------------------------------------------------------------
        // Phase SETUP (1 cycle)
        // -----------------------------------------------------------------
        // TODO: Mettre PSEL=1, PENABLE=0
        // TODO: Positionner PADDR, PWRITE, PWDATA
        vif.driver_cb.psel    <= 1'b1;
        vif.driver_cb.penable <= 1'b0;
        vif.driver_cb.paddr   <= txn.addr;
        vif.driver_cb.pwrite  <= txn.write;
        vif.driver_cb.pwdata  <= txn.wdata;

        @(posedge vif.pclk);

        // -----------------------------------------------------------------
        // Phase ACCESS (1+ cycles)
        // -----------------------------------------------------------------
        // TODO: Mettre PENABLE=1
        vif.driver_cb.penable <= 1'b1;

        // TODO: Attendre que PREADY=1
        // Utilise: wait(vif.driver_cb.pready)
        @(posedge vif.pclk);
        while (!vif.driver_cb.pready) begin
            @(posedge vif.pclk);
        end

        // TODO: Capturer les données de lecture et l'erreur
        if (!txn.write) begin
            txn.rdata = vif.driver_cb.prdata;
        end
        txn.slverr = vif.driver_cb.pslverr;

        // -----------------------------------------------------------------
        // Retour à IDLE
        // -----------------------------------------------------------------
        vif.driver_cb.psel    <= 1'b0;
        vif.driver_cb.penable <= 1'b0;

        `uvm_info(get_name(), $sformatf("Drove: %s", txn.convert2string()), UVM_MEDIUM)

    endtask

endclass
