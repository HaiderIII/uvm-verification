// ============================================================================
// APB Test
// ============================================================================
// Le test est le point d'entrée du testbench UVM
// Il crée l'environnement et lance les séquences
// ============================================================================

class apb_base_test extends uvm_test;

    // =========================================================================
    // Enregistrement UVM
    // =========================================================================
    `uvm_component_utils(apb_base_test)

    // =========================================================================
    // Environnement
    // =========================================================================
    apb_env env;

    // =========================================================================
    // Constructeur
    // =========================================================================
    function new(string name = "apb_base_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    // =========================================================================
    // Build Phase
    // =========================================================================
    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        // Créer l'environnement
        env = apb_env::type_id::create("env", this);
    endfunction

    // =========================================================================
    // Run Phase - Lancer la séquence
    // =========================================================================
    virtual task run_phase(uvm_phase phase);
        apb_full_test_seq seq;

        // Lever l'objection (empêche la simulation de se terminer)
        phase.raise_objection(this);

        // Attendre un peu après le reset
        #100ns;

        // Créer et lancer la séquence
        seq = apb_full_test_seq::type_id::create("seq");
        seq.start(env.agent.sequencer);

        // Attendre que tout soit terminé
        #100ns;

        // Baisser l'objection (permet à la simulation de se terminer)
        phase.drop_objection(this);
    endtask

endclass
