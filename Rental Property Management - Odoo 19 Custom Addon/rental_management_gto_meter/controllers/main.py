# -*- coding: utf-8 -*-
import logging

from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)


class SmartMeterIoTController(http.Controller):

    @http.route('/api/v1/meter/iot_reading', type='jsonrpc', auth='none',
                methods=['POST'], csrf=False)
    def receive_iot_meter_reading(self, **kwargs):
        """Receive IoT smart meter readings via REST webhook.

        Expected JSON payload::

            {
                "meter_code": "MET-001",
                "current_reading": 12345.67,
                "reading_type": "electricity",   # optional
                "api_key": "YOUR_SECRET_KEY"
            }
        """
        data = request.jsonrequest or {}

        # --- BUG-02 FIX: API Key authentication -------------------------
        api_key = (data.get('api_key')
                   or request.httprequest.headers.get('X-API-Key', ''))
        expected_key = (request.env['ir.config_parameter']
                        .sudo()
                        .get_param('meter.iot_api_key', ''))
        if not expected_key:
            _logger.warning(
                "IoT meter API key not configured "
                "(System Parameter 'meter.iot_api_key'). "
                "Rejecting all requests until configured.")
            return {'status': 'error',
                    'message': 'IoT API key not configured on server'}
        if api_key != expected_key:
            _logger.warning("IoT meter auth failed for key: %s…",
                            api_key[:8] if api_key else '(empty)')
            return {'status': 'error', 'message': 'Unauthorized'}

        # --- Validate payload -------------------------------------------
        meter_code = data.get('meter_code')
        reading_val = data.get('current_reading')

        if not meter_code or reading_val is None:
            return {'status': 'error',
                    'message': 'Missing meter_code or current_reading'}

        try:
            reading_val = float(reading_val)
        except (ValueError, TypeError):
            return {'status': 'error',
                    'message': 'current_reading must be a number'}

        # --- BUG-01 FIX: Search the correct model (property.meter) ------
        meter = (request.env['property.meter']
                 .sudo()
                 .search([('name', '=', meter_code)], limit=1))
        if not meter:
            return {'status': 'error',
                    'message': 'Meter with code %s not found' % meter_code}

        # Create a new reading record instead of overwriting
        previous = meter.last_reading or 0.0
        if reading_val < previous:
            _logger.info(
                "IoT reading for %s (%s) is lower than previous (%s). "
                "Possible meter reset.", meter_code, reading_val, previous)

        reading = request.env['property.meter.reading'].sudo().create({
            'meter_id': meter.id,
            'date': fields.Date.today(),
            'previous_reading': previous,
            'current_reading': reading_val,
            'tariff': meter.tariff,
            'tenancy_id': meter.tenancy_id.id if meter.tenancy_id else False,
        })
        _logger.info("IoT reading created: %s for meter %s (val=%s)",
                      reading.name, meter_code, reading_val)

        return {
            'status': 'success',
            'message': 'Meter reading created for %s' % meter_code,
            'reading_id': reading.id,
            'reading_ref': reading.name,
            'current_reading': reading_val,
            'consumption': reading.consumption,
        }
