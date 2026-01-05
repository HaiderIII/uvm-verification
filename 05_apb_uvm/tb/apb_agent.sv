// ============================================================================
// APB Agent
// ============================================================================
// Conteneur qui regroupe: Driver + Monitor + Sequencer
// Peut être ACTIVE (driver + monitor) ou PASSIVE (monitor seul)
// ============================================================================

class apb_agent extends uvm_agent;

    // =========================================================================
    // Enregistrement UVM
    // =========================================================================
    `uvm_component_utils(apb_agent)

    // =========================================================================
    // Composants
    // =========================================================================
    apb_driver    driver;
    apb_monitor   monitor;
    uvm_sequencer #(apb_seq_item) sequencer;

    // =========================================================================
    // Constructeur
    // =========================================================================
    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    // =========================================================================
    // Build Phase - Créer les composants
    // =========================================================================
    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        // Le monitor est TOUJOURS créé
        monitor = apb_monitor::type_id::create("monitor", this);

        // Le driver et sequencer sont créés seulement en mode ACTIVE
        // is_active est une propriété héritée de uvm_agent
        if (is_active == UVM_ACTIVE) begin
            driver    = apb_driver::type_id::create("driver", this);
            sequencer = uvm_sequencer#(apb_seq_item)::type_id::create("sequencer", this);
        end
    endfunction

    // =========================================================================
    // Connect Phase - Connecter driver <-> sequencer
    // =========================================================================
    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);

        // Connecter le driver au sequencer (seulement en mode ACTIVE)
        if (is_active == UVM_ACTIVE) begin
            driver.seq_item_port.connect(sequencer.seq_item_export);
        end
    endfunction

endclass
