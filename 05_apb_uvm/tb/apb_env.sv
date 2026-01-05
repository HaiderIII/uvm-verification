// ============================================================================
// APB Environment
// ============================================================================
// Conteneur principal: Agent + Scoreboard
// Connecte le monitor au scoreboard
// ============================================================================

class apb_env extends uvm_env;

    // =========================================================================
    // Enregistrement UVM
    // =========================================================================
    `uvm_component_utils(apb_env)

    // =========================================================================
    // Composants
    // =========================================================================
    apb_agent      agent;
    apb_scoreboard scoreboard;

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

        // Créer l'agent (mode ACTIVE par défaut)
        agent = apb_agent::type_id::create("agent", this);

        // Créer le scoreboard
        scoreboard = apb_scoreboard::type_id::create("scoreboard", this);
    endfunction

    // =========================================================================
    // Connect Phase - Connecter monitor -> scoreboard
    // =========================================================================
    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);

        // Connecter l'analysis_port du monitor à l'analysis_export du scoreboard
        agent.monitor.analysis_port.connect(scoreboard.analysis_export);
    endfunction

endclass
