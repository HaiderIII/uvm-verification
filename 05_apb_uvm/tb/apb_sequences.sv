// ============================================================================
// APB Sequences
// ============================================================================
// Les séquences génèrent les transactions pour le driver
// ============================================================================

// =============================================================================
// Séquence de base - Une seule transaction
// =============================================================================
class apb_base_seq extends uvm_sequence #(apb_seq_item);

    `uvm_object_utils(apb_base_seq)

    function new(string name = "apb_base_seq");
        super.new(name);
    endfunction

    virtual task body();
        req = apb_seq_item::type_id::create("req");

        start_item(req);
        if (!req.randomize()) begin
            `uvm_error(get_name(), "Randomization failed")
        end
        finish_item(req);
    endtask

endclass

// =============================================================================
// Séquence Write-Read - Écrit puis relit la même adresse
// =============================================================================
class apb_write_read_seq extends uvm_sequence #(apb_seq_item);

    `uvm_object_utils(apb_write_read_seq)

    rand bit [7:0]  addr;
    rand bit [31:0] data;

    constraint addr_c {
        addr[1:0] == 2'b00;
        addr <= 8'h0C;
    }

    function new(string name = "apb_write_read_seq");
        super.new(name);
    endfunction

    virtual task body();
        // Écriture
        req = apb_seq_item::type_id::create("req");
        start_item(req);
        req.write = 1;
        req.addr  = addr;
        req.wdata = data;
        finish_item(req);

        // Lecture
        req = apb_seq_item::type_id::create("req");
        start_item(req);
        req.write = 0;
        req.addr  = addr;
        finish_item(req);
    endtask

endclass

// =============================================================================
// Séquence complète - Test tous les registres
// =============================================================================
class apb_full_test_seq extends uvm_sequence #(apb_seq_item);

    `uvm_object_utils(apb_full_test_seq)

    function new(string name = "apb_full_test_seq");
        super.new(name);
    endfunction

    virtual task body();
        bit [7:0] addrs [4] = '{8'h00, 8'h04, 8'h08, 8'h0C};
        bit [31:0] test_data [4] = '{32'hDEADBEEF, 32'hCAFEBABE, 32'h12345678, 32'hAAAABBBB};

        // Écrire tous les registres
        foreach (addrs[i]) begin
            req = apb_seq_item::type_id::create("req");
            start_item(req);
            req.write = 1;
            req.addr  = addrs[i];
            req.wdata = test_data[i];
            finish_item(req);
        end

        // Relire tous les registres
        foreach (addrs[i]) begin
            req = apb_seq_item::type_id::create("req");
            start_item(req);
            req.write = 0;
            req.addr  = addrs[i];
            finish_item(req);
        end

        // Quelques transactions aléatoires
        repeat (10) begin
            req = apb_seq_item::type_id::create("req");
            start_item(req);
            if (!req.randomize()) begin
                `uvm_error(get_name(), "Randomization failed")
            end
            finish_item(req);
        end
    endtask

endclass
