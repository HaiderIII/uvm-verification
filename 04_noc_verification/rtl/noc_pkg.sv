// ============================================================================
// NoC Package - Définitions communes
// ============================================================================

package noc_pkg;

    // =========================================================================
    // Paramètres du réseau
    // =========================================================================
    parameter COORD_WIDTH = 4;          // Coordonnées sur 4 bits (mesh 16x16 max)
    parameter DATA_WIDTH = 32;          // Données sur 32 bits
    parameter PACKET_WIDTH = 64;        // Largeur totale du paquet

    // =========================================================================
    // Types de paquets
    // =========================================================================
    typedef enum logic [3:0] {
        PKT_READ_REQ  = 4'b0001,        // Requête de lecture
        PKT_WRITE_REQ = 4'b0010,        // Requête d'écriture
        PKT_RESPONSE  = 4'b0100,        // Réponse (données)
        PKT_ACK       = 4'b1000         // Acquittement
    } packet_type_t;

    // =========================================================================
    // Directions de routage
    // =========================================================================
    typedef enum logic [2:0] {
        DIR_LOCAL = 3'd0,
        DIR_NORTH = 3'd1,
        DIR_SOUTH = 3'd2,
        DIR_EAST  = 3'd3,
        DIR_WEST  = 3'd4
    } direction_t;

    // =========================================================================
    // Structure du paquet NoC
    // =========================================================================
    //
    //  63      60 59    56 55    52 51    48 47                              0
    // ┌─────────┬────────┬────────┬────────┬─────────────────────────────────┐
    // │  TYPE   │ SRC_X  │ SRC_Y  │ DST_X  │ DST_Y  │        PAYLOAD         │
    // │ 4 bits  │ 4 bits │ 4 bits │ 4 bits │ 4 bits │        44 bits         │
    // └─────────┴────────┴────────┴────────┴────────┴────────────────────────┘
    //
    // Note: Pour simplifier, on utilise 64 bits avec:
    // - [63:60] : Type (4 bits)
    // - [59:56] : Source X (4 bits)
    // - [55:52] : Source Y (4 bits)
    // - [51:48] : Dest X (4 bits)
    // - [47:44] : Dest Y (4 bits)
    // - [43:0]  : Payload (44 bits, inclut adresse + données)

    // Positions des champs dans le paquet
    parameter TYPE_MSB  = 63;
    parameter TYPE_LSB  = 60;
    parameter SRC_X_MSB = 59;
    parameter SRC_X_LSB = 56;
    parameter SRC_Y_MSB = 55;
    parameter SRC_Y_LSB = 52;
    parameter DST_X_MSB = 51;
    parameter DST_X_LSB = 48;
    parameter DST_Y_MSB = 47;
    parameter DST_Y_LSB = 44;
    parameter PAYLOAD_MSB = 43;
    parameter PAYLOAD_LSB = 0;

    // =========================================================================
    // Fonctions d'extraction des champs
    // =========================================================================

    function automatic logic [3:0] get_type(input logic [PACKET_WIDTH-1:0] pkt);
        return pkt[TYPE_MSB:TYPE_LSB];
    endfunction

    function automatic logic [3:0] get_src_x(input logic [PACKET_WIDTH-1:0] pkt);
        return pkt[SRC_X_MSB:SRC_X_LSB];
    endfunction

    function automatic logic [3:0] get_src_y(input logic [PACKET_WIDTH-1:0] pkt);
        return pkt[SRC_Y_MSB:SRC_Y_LSB];
    endfunction

    function automatic logic [3:0] get_dst_x(input logic [PACKET_WIDTH-1:0] pkt);
        return pkt[DST_X_MSB:DST_X_LSB];
    endfunction

    function automatic logic [3:0] get_dst_y(input logic [PACKET_WIDTH-1:0] pkt);
        return pkt[DST_Y_MSB:DST_Y_LSB];
    endfunction

    function automatic logic [43:0] get_payload(input logic [PACKET_WIDTH-1:0] pkt);
        return pkt[PAYLOAD_MSB:PAYLOAD_LSB];
    endfunction

    // =========================================================================
    // Fonction de création de paquet
    // =========================================================================
    function automatic logic [PACKET_WIDTH-1:0] make_packet(
        input logic [3:0]  pkt_type,
        input logic [3:0]  src_x,
        input logic [3:0]  src_y,
        input logic [3:0]  dst_x,
        input logic [3:0]  dst_y,
        input logic [43:0] payload
    );
        return {pkt_type, src_x, src_y, dst_x, dst_y, payload};
    endfunction

endpackage
